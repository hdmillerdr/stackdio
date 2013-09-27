define(["knockout",
        "lib/q", 
        "app/util/form",
        "app/viewmodel/abstract",
        "app/model/models",
        "app/store/stores",
        "app/api/api"], 
    function (ko, Q, formutils, abstractVM, models, stores, API) {

        var vm = function () {
            var self = this;
            self.selectedAccount = null;
            self.selectedSecurityGroup = null;

            // Navigation properties
            self.showPagination = ko.observable(false);
            self.nextLink = ko.observable(null);
            self.previousLink = ko.observable(null);

            self.addSecurityGroup = function (name, evt) {
                var record = {};
                record.name = name;
                record.cloud_provider = self.selectedAccount.id;
                record.is_default = false;
                record.description = "";

                API.SecurityGroups.save(record)
                    .then(function (newGroup) {
                        /*
                            Add the group to both SecurityGroups (all groups for this user)
                            and AccountSecurityGroups (all groups for the chosen account)
                        */
                        var group = new models.SecurityGroup().create(newGroup);
                        group.account = _.find(stores.Accounts(), function (a) {
                            return a.id === group.provider_id;
                        })

                        stores.SecurityGroups.push(group);
                        stores.AccountSecurityGroups.push(group);

                        // Clear the form and close it
                        formutils.clearForm('securitygroup-form');
                        self.closeSecurityGroupForm();
                        
                    })
                    .catch(function (error) {
                        console.error(error.toString());
                    })
            };

            self.capture = function (model, evt) {
                if (evt.charCode === 13) {
                    self.addDefaultSecurityGroup(document.getElementById('new_securitygroup_name').value);
                    return false;
                }
                return true;
            };

            self.captureNewGroup = function (model, evt) {
                if (evt.charCode === 13) {
                    self.addSecurityGroup(document.getElementById('securitygroup_name').value);
                    return false;
                }
                return true;
            };

            self.addDefaultSecurityGroup = function (name, evt) {
                var record = {};
                record.name = name;
                record.cloud_provider = self.selectedAccount.id;
                record.is_default = true;
                record.description = "";

                API.SecurityGroups.save(record)
                    .then(function () {
                        formutils.clearForm('default-securitygroup-form');
                        self.listDefaultGroups(self.selectedAccount);
                    })
                    .catch(function (error) {
                        $("#alert-error").show();
                    })
            };

            self.deleteDefaultSecurityGroup = function (groupId) {
                console.log('group to delete', groupId);
                var record = _.findWhere(stores.DefaultSecurityGroups(), { id: parseInt(groupId, 10) });
                console.log('found record', record);

                if (typeof record !== 'undefined') {
                    record.is_default = false;

                    API.SecurityGroups.updateDefault(record)
                        .then(function () {
                            self.listDefaultGroups(self.selectedAccount);
                        })
                        .catch(function (error) {
                            $("#alert-error").show();
                        });
                }
            };

            self.listDefaultGroups = function (account) {
                $('#default_group_list').empty();

                // For each security group that is default, add a label styled span element in the UI
                _.each(stores.DefaultSecurityGroups(), function (g) {
                    if (g.is_default && g.provider_id === account.id) {
                        $('#default_group_list').append('<span id="defaultgroup_'+ g.id +'" style="cursor: pointer; margin: 0 5px;" defaultlabel class="label label-success"><span class="iconic-x"></span> '+ g.name +'</span>');
                    }
                });

                // Handle the user clicking on the group label to set the group to is_default:false
                $('span[defaultlabel]').click(function (evt) {
                    var groupId = evt.target.id.split('_')[1];
                    self.deleteDefaultSecurityGroup(groupId);
                });
            };

            self.setForAccount = function (account) {
                if (!account.hasOwnProperty('security_group') || !account.hasOwnProperty('yaml')) {
                    var accountsLength = stores.Accounts().length;
                    var account = stores.Accounts()[accountsLength - 1];
                }
                self.selectedAccount = account;

                API.SecurityGroups.loadByAccount(account)
                    .then(function () {
                        self.listDefaultGroups(account);
                    });
                self.showDefaultGroupForm();
            };

            self.deleteSecurityGroup = function (group) {
                API.SecurityGroups.delete(group)
                    .then(self.showSuccess)
                    .catch(function (error) {
                        self.showError(error.toString(), 5000);
                    });
            };

            self.deleteGroupRule = function (rule) {
                rule.action = "revoke";

                API.SecurityGroups.updateRule(self.selectedSecurityGroup, rule)
                    .then(self.showSuccess)
                    .catch(function (error) {
                        self.showError(error.toString(), 5000);
                    });
            };

            self.editGroupRules = function (group) {
                self.selectedSecurityGroup = group;
                stores.SecurityGroupRules.removeAll();

                _.each(group.rules, function (r) {
                    stores.SecurityGroupRules.push(new models.SecurityGroupRule().create(r));
                });

                $("#securitygroup-rules-form-container").dialog("open");
            };

            self.addRule = function (model, evt) {
                var record = formutils.collectFormFields(evt.target.form);
                var rule;

                if (record.rule_ip_address.value !== '') {
                    rule = record.rule_ip_address.value;
                } else if (record.rule_group.value !== '') {
                    rule = record.rule_group.value;
                }

                API.SecurityGroups.updateRule(self.selectedSecurityGroup, {
                    action: 'authorize',
                    protocol: record.rule_protocol.value,
                    from_port: record.rule_from_port.value,
                    to_port: record.rule_to_port.value,
                    rule: rule
                })
                    .then(function () {
                        self.showSuccess();
                        formutils.clearForm('group-rule-form');
                        $("#new-rule-dialog").dialog("close");
                    })
                    .catch(function (error) {
                        self.showError(error.toString(), 5000);
                    });
            };

            self.closeRulesForm = function () {
                $("#securitygroup-rules-form-container").dialog("close");
            };

            self.paginate = function (url) {
                API.SecurityGroups.load(url)
                    .then(function (properties) {
                        console.log(properties);
                        
                        if (properties.count > stackdio.settings.pageSize) {
                            self.showPagination(true);
                            self.nextLink(properties.next);
                            self.previousLink(properties.previous);
                        }

                    });
            };

            self.loadSecurityGroups = function () {
                return API.SecurityGroups.load()
                    .then(function (properties) {

                        if (properties.count > stackdio.settings.pageSize) {
                            self.showPagination(true);
                            self.nextLink(properties.next);
                            self.previousLink(properties.previous);
                        }

                    });
            };

            self.showSecurityGroupForm = function (account) {
                self.selectedAccount = account;
                $("#securitygroup-form-container").dialog("open");
            };

            self.showDefaultGroupForm = function () {
                $("#default-securitygroup-form-container").dialog("open");
                $("#alert-default-security-groups").hide();
            };

            self.closeSecurityGroupForm = function (type) {
                $("#securitygroup-form-container").dialog("close");
            };

            /*
             *  ==================================================================================
             *  D I A L O G   E L E M E N T S
             *  ==================================================================================
             */
            $("#securitygroup-form-container").dialog({
                autoOpen: false,
                width: 500,
                modal: false
            });

            $("#default-securitygroup-form-container").dialog({
                autoOpen: false,
                width: 800,
                modal: false
            });

            $("#securitygroup-rules-form-container").dialog({
                autoOpen: false,
                width: 800,
                modal: true
            });

            $("#new-rule-dialog").dialog({
                autoOpen: false,
                width: 500,
                modal: true
            });

        };

        vm.prototype = new abstractVM();

        return vm;
});