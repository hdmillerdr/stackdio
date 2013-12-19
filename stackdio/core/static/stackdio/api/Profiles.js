define(["q", "store/stores", "model/models"], function (Q, stores, models) {
    return {
        load : function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/profiles/',
                type: 'GET',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (data, status, response) {
                    var i, item, items = data.results;
                    var profile;

                    // Clear the store and the grid
                    stores.Profiles.removeAll();

                    for (i in items) {
                        profile = new models.Profile().create(items[i]);

                        // Inject the name of the provider account used to create the profile
                        profile.account = _.find(stores.Accounts(), function (account) {
                            return account.id === profile.cloud_provider;
                        });

                        // Inject the record into the store
                        stores.Profiles.push(profile);
                    }

                    console.log('profiles', stores.Profiles());

                    // Resolve the promise
                    deferred.resolve();

                }
            });

            return deferred.promise;
        },
        save: function (record) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/profiles/',
                type: 'POST',
                data: {
                    title: record.profile_title.value,
                    description: record.profile_description.value,
                    cloud_provider: record.account.id,
                    image_id: record.image_id.value,
                    default_instance_size: record.default_instance_size.value,
                    ssh_user: record.ssh_user.value
                },
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, profile = response;

                    if (profile.hasOwnProperty('id')) {
                        // Inject the name of the provider account used to create the profile
                        profile.account = _.find(stores.Accounts(), function (account) {
                            return account.id === profile.cloud_provider;
                        });

                        stores.Profiles.push(profile);
                        deferred.resolve(profile);
                    }
                }
            });

            return deferred.promise;
        },
        delete: function (profile) {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/profiles/' + profile.id,
                type: 'DELETE',
                headers: {
                    "X-CSRFToken": stackdio.settings.csrftoken,
                    "Accept": "application/json"
                },
                success: function (response) {
                    stores.Profiles.remove(profile);
                    deferred.resolve(profile);
                },
                error: function (request, status, error) {
                    deferred.reject(new Error(error));
                }
            });

            return deferred.promise;
        }
    }
});