 'use strict';
  
 var kittyControllers = angular.module('kittyControllers', []);
  /* Controllers */
 
 kittyControllers.
 controller('RootCtrl', ['$scope', '$http',
                            function($scope, $http) {
     var updateCommentStatus = function () {
            $http.get('/comment-unread').then(
                function success(response) {
                     $scope.unreadCommentsCount = response.data.count;
                     $scope.unreadComments = response.data.data;
                },
                function failure() {}
            );
         },
         updateVotesStatus = function () {
            $http.get('/count-author-rhyme-votes').then(
                function success(response) {
                     $scope.commentsVotesStrength = response.data.strength;
                     $scope.commentsVotes = response.data.data;
                },
                function failure() {}
            );
         };
     $scope.unreadCommentsCount = '-';
     $scope.commentsVotesStrenggth = '-';
     $scope.unreadComments = [];
     $scope.commentsVotes = [];
     $('#trigger-comments-unread').popover({
        html : true,
        trigger: "click hover",
        placement: 'bottom',
        delay: {
           show: "200",
           hide: "10000"
        },
        content: function(e) {
            return $('#popover-comments-unread').html();
        }
    });
    $('#trigger-comments-votes').popover({
        html : true,
        trigger: "click hover",
        placement: 'bottom',
        delay: {
           show: "200",
           hide: "500"
        },
        content: function(e) {
            return $('#popover-comments-votes').html();
        }
    });
    updateCommentStatus();
    updateVotesStatus();
    $('#trigger-comments-unread').click(function(e){e.preventDefault();});

    $scope.$on('commentsSaw', function (e, comments) {
        $http.post('/comment-mark-as-read/json', comments).then(
            function success() {
                updateCommentStatus();
            },
            function failure() {}
        );
    });
 }]).
 controller('PopoverCommentsCtrl', ['$scope', '$http',
                                    function($scope, $http) {
    $scope.popoverComments = function(e, rhymeId, url) {
        $http.get(url).then(
            function success (response) {
                $scope.comments = response.data.data;
                $('#popover-' + rhymeId).show('fast');
                setTimeout(function () {
                    $('#popover-' + rhymeId).hide('slow');
                    $scope.$emit('commentsSaw', JSON.stringify($scope.comments));
                }, 10000);
            },
            function failure (response) {

            }
        );
    };
    $scope.comments = [];
 }]).
 controller('StoreCtrl', ['$scope', '$http',
                            function ($scope, $http) {
    $scope.stores = [];
    $scope.storeChange = function (e, afterUrl, afterLabel, index) {
        e.preventDefault();
        if (typeof $scope.stores[index] === 'undefined') {
            $scope.stores[index] = {}
            $scope.stores[index].url = e.target.href,
            $scope.stores[index].label = e.target.innerHTML.trim();
            $scope.stores[index].afterUrl = afterUrl;
            $scope.stores[index].afterLabel = afterLabel;
            $scope.stores[index].stateAfter = true;
        }
        var action = ($scope.stores[index].stateAfter === true) ? $scope.stores[index].url : $scope.stores[index].afterUrl;
        $http.post(action).then(
            function success (response) {
                if ($scope.stores[index].stateAfter === true) {
                    e.target.href = $scope.stores[index].afterUrl;
                    e.target.innerHTML = $scope.stores[index].afterLabel;
                } else {
                    e.target.href = $scope.stores[index].url;
                    e.target.innerHTML = $scope.stores[index].label;
                }
                $scope.stores[index].stateAfter = ! $scope.stores[index].stateAfter;
            },
            function failure (response) {

            }
        )

    }

 }]).
 controller('RhymeCtrl',['$scope', '$http',
                            function RhymeListCtrl($scope, $http) {
    if (typeof $scope.rhymes === 'undefined') $scope.rhymes = [];
    if (typeof $scope.fields === 'undefined') $scope.fields = {};
    $scope.formState = 'Dodawanie';
    var rhymes = $('[rhyme]');
    rhymes.each(function(it) {
        var rhyme = $(rhymes[it]);
        $scope.rhymes[it + 1] = {
            'id': rhyme.find('id').html(),
            'title': rhyme.find('title').html(),
            'content': rhyme.find('content').html(),
            'category': rhyme.find('category').html()
        };
    });

    $scope.remove = function remove (e, loopCounter) {
        e.preventDefault();
        $scope.modalTitle = 'Usunąć wiersz "' + $scope.rhymes[loopCounter].title + '"?';
        $scope.modalBody = 'Usunięcie danych jest nieodwracalne, potwierdź decyzję';
        $scope.modalPrimaryBtn = 'Usuń';
        $scope.modalCloseBtn = 'Zamknij';
        $scope.modalConfirmAction = function (event) {
            angular.element('#modal').modal('hide');
            $http.
                delete(e.currentTarget.href).
                then(
                    function success (response) {
                        angular.element('#rhyme-id-' + loopCounter).remove();
                        document.location.reload();
                    }
                );
        }
        angular.element('#modal').modal('show');
    };

    $scope.edit = function edit (e, loopCounter) {
        e.preventDefault();
        $scope.formState = 'Edycja';
        $scope.formAction = e.currentTarget.href;

        if (false === angular.element('#demo').hasClass('in')){
            angular.element('button[data-target=#demo]').click();
        }
        window.location.hash = '#demo';

        $scope.fields.title = $scope.rhymes[loopCounter].title;
        $scope.fields.content = $scope.rhymes[loopCounter].content;
        tinyMCE.activeEditor.setContent($scope.rhymes[loopCounter].content, {format : 'raw'});
        $scope.fields.category = $scope.rhymes[loopCounter].category;
    };

	$scope.add = function add (e) {

        $scope.errors = {};
        $scope.fields.content = tinyMCE.activeEditor.getContent();
        $http.
            post(e.currentTarget.action, $scope.fields).
            then(
                function success (response) {
                    var data = response.data;
                    if (data.valid) {
                        document.location.reload();
                    } else {
                        var errors = data.errors;
                        for (var i in errors) {
                            $scope.errors[errors[i][0]] = errors[i][1];
                        }
                    }
                },
                function failure (response) {

                }
            );
    };
    $scope.close = function close (e) {
        e.preventDefault();
        $scope.formAction = '';
        $scope.formState = 'Dodawanie';
        $scope.fields.title = '';
        $scope.fields.content = ''
        tinyMCE.activeEditor.setContent('', {format : 'raw'});
        $scope.fields.category = '';
        if (true === angular.element('#demo').hasClass('in')){
            angular.element('button[data-target=#demo]').click();
        }
    };
 }]).
 controller('VoteRhymeCtrl', ['$scope', '$http',
                        function VoteRhymeCtrl($scope, $http) {
    var initPopover = function (id) {
        var pop = $('[name=trigger-vote-' + id + ']');
        pop.popover({
            html : true,
            trigger: "hover",
            delay: 300,
            placement: 'left',
            content: function(e) {
                return $('#popover-vote-' + id).html();
            }
        });
        return pop;
    };

    $scope.showVoters = function (e, rhymeId) {
        initPopover(rhymeId);
        $http.get('/voters/' + rhymeId).then(
            function success(response) {
                $scope.voters = response.data.data;

            },
            function failure() {}
        );
    }

    $scope.vote = function (e) {
        e.preventDefault();
        $http.get(e.currentTarget.href).success(function (data) {
            e.target.textContent = ' ' + data.strength;
        });
    };
 }]);