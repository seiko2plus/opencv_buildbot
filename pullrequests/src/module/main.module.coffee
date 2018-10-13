pullrequestsTemplate = require './pullrequests.tpl.jade'

class app extends App
    constructor: ->
        return [
            'ui.router'
            'ui.bootstrap'
            'ngAnimate'
            'guanlecoja.ui'
            'bbData'
    ]


class State extends Config
    constructor: ($stateProvider, glMenuServiceProvider, config) ->
        for pulls, index in config.plugins.pullrequests
            # Name of the state
            name = "#{pulls.name}_pullrequests"

            # Menu configuration
            glMenuServiceProvider.addGroup
                name: name
                caption: pulls.caption
                icon: pulls.icon
                order: 2 + index

            # Configuration
            cfg =
                group: name
                caption: pulls.caption
                name: pulls.name

            # Register new state
            state =
                controller: "pullrequestsController"
                controllerAs: "c"
                template: pullrequestsTemplate
                name: name
                url: "/#{name}"
                data: cfg

            $stateProvider.state(state)

class Pullrequests extends Controller
    constructor: ($scope, $state, $interval, $http, dataService) ->
        @requests = `undefined`
        @builders = dataService.open().closeOnDestroy($scope).getBuilders()

        name = $state.current.data.name
        fetchPulls = (() ->
            $http.get('/pullrequests/api/' + name).then (@parseRequests.bind this)
        ).bind this

        @builders.onChange = fetchPulls
        req_tck = $interval(fetchPulls, 10000)

        $scope.$on '$destroy', ->
            $interval.cancel req_tck

    getPullrequests: () ->
        $$ = @
        @$http.get('/pullrequests/api/' + @name).then (response) ->
            $$.parseRequests response

    parseRequests: (response) ->
        requests = []
        for request in response.data
            builds = []
            for bid, build of request['builds']
                [rid, cid, status] = build
                build = {}

                if cid is null
                    build['url'] = '/#/buildrequests/' + rid
                else
                    build['url'] = "#/builders/#{bid}/builds/#{cid}"

                status = @statusName status
                c_lass = 'results_' + status
                if status is 'PENDING'
                    c_lass += ' pulse'

                build['status'] = status
                build['class'] = c_lass
                build['name'] = @builders.get(bid)['name']
                builds.push build

            if request['assignee'] is null
                request['assignee'] = 'None'

            request['builds'] = builds
            requests.push request

        if @requests is `undefined` or not @objCMP(requests, @requests)
            console.log 'something change here buddy'
            @requests = requests

    objCMP: (a, b) ->
        if a.length isnt b.length
            return false

        for k, v of a
            if k is '$$hashKey'
                continue

            vb = b[k]
            tp_vb = typeof(vb)

            if typeof(v) isnt tp_vb
                return false

            if tp_vb is 'object'
                if not @objCMP(vb, v)
                    return false
                continue

            if v isnt vb
                return false

        return true

    statusName: (num) ->
        names = ['UNKNOWN', 'PENDING', 'SUCCESS', 'WARNINGS',
        'FAILURE', 'SKIPPED', 'EXCEPTION', 'RETRY', 'CANCELLED']
        return names[num]