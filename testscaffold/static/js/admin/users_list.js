// is is only test controller for demo purposes
demoApp = angular.module('demoApp');
demoApp.controller('UserListController', UserListController);

function UserListController($http) {
    var vm = this;
    // Any function returning a promise object can be used to load values asynchronously
    vm.getUsers = function (val) {

        return $http.get(API_BASE_URL + '/users', {
            params: {
                user_name_like: val
            }
        }).then(function (response) {
            return response.data.map(function (item) {
                return item;
            });
        });
    };

    vm.assignUserToGroup = function (groupId) {
        console.log('assignUserToGroup');
        return $http.post(API_BASE_URL + '/groups/' + groupId + '/users', {
            user_id: vm.selectedUser.id
        }).then(function (response) {
            window.location.reload(true);
        });
    }
}
