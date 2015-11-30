app.controller('ResourceCtrl', ['$scope','$http', 'toaster',"$rootScope", function($scope,$http, toaster,$rootScope){
$scope.addResModal = false;
    $scope.editResModal = false;
    $scope.triggerAddResModal = function(){
        $scope.addResModal = true;
        console.log($scope.editResModal)
        $scope.newResource = {};
    };
    $scope.showEditResModal = function(name,id){
    	$scope.editResObj={
            'name':name,
    		'id':id
    	};

    	$scope.editResModal = true;
        console.log($scope.editResModal)
    }
    $scope.editResource = function(editResObj){
        if(!editResObj.name || !editResObj.id){
            return;
        }
        console.log($scope.editResModal)
        $http({
        method:"PUT",
        url:"/api/resources",
        data:{
          "resource_name": editResObj['name'],
          "resource_id" :  editResObj['id']
        }
        }).then(function successCallback(data) {
            $scope.loadRes()
            $scope.editResModal = false;
            console.log($scope.editResModal)
            $scope.msg.editSuccess('ресурсу');
        }, function errorCallback(response) {
            $scope.msg.editError('ресурсу');
            console.log($scope.editResModal)
        })

    };


   	$scope.deleteResource = function(id){
        $http({
          method:"DELETE",
          headers: {"Content-Type": "application/json;charset=utf-8"},
          url:"/api/resources",
          data:{
            "resource_id":id
          }
        }).then(function successCallback(data) {
            $scope.loadRes()
            $scope.msg.deleteSuccess('ресурсу');
        }, function errorCallback(response) {
            $scope.msg.deleteError('ресурсу');
        })
   	};

    $scope.newResource = {};
    $scope.addResource = function(newResource){
        console.log($scope.Roles)
        if(!newResource.name){
            return;
        }

         $http({
            method: "POST",
            url: "/api/resources",
            data:{
                'resource_name': $scope.newResource.name
            }
        }).then(function successCallback(data) {
        $scope.addResModal = false;
        $scope.Resources[data.data.added_resource]=data.data.resource_id
        console.log($scope.addResModal)
        $scope.msg.createSuccess('ресурсу');
        }, function errorCallback(response) {
            $scope.addResModal=false
            $scope.msg.createError('ресурсу');
        });

    };
}])