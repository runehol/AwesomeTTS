/*
 * AwesomeTTS text-to-speech add-on website
 *
 * Copyright (C) 2014       Anki AwesomeTTS Development Team
 * Copyright (C) 2014       Dave Shifflett
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * Gruntfile for AwesomeTTS website and update API service
 *
 * Provides Grunt tasks for building the project, running it locally, and
 * deploying it to Google App Engine with a git-derived version.
 *
 * Examples:
 *     $ grunt build      # builds project to the build/ subdirectory
 *
 *     $ grunt deploy     # builds project and sends new version to GAE
 *
 *     $ grunt run        # builds project and then runs the GAE SDK server
 *                        # with its logging output sent to the console
 *
 *     $ grunt watch      # monitors file system to automatically rebuild the
 *                        # project as needed (but does NOT do initial build)
 *
 *     $ grunt run watch  # combines the above two, but the GAE SDK server is
 *                        # backgrounded, so only watch activity is visible
 *
 *     $ grunt clean      # removes the contents of build/ subdirectory
 */

/*jslint indent:4*/
/*jslint node:true*/
/*jslint regexp:true*/

module.exports = function (grunt) {
    'use strict';

    var doWatch = grunt.cli.tasks.indexOf('watch') !== -1;

    var SITEMAP = grunt.file.readJSON('sitemap.json');

    var config = {pkg: 'package.json'};
    grunt.config.init(config);


    // Task Aliases //////////////////////////////////////////////////////////

    grunt.task.registerTask('default', 'help');
    grunt.task.registerTask('help', "Display usage.", grunt.help.display);

    grunt.task.registerTask('build', "Build all into build subdirectory.", [
        'clean', 'copy', 'json-minify', 'cssmin', 'mustache_render',
        'htmlmin', 'appyaml',
    ]);

    grunt.task.registerTask('run', "Runs project locally using GAE SDK.", [
        'build', 'gae:run',
    ]);

    grunt.task.registerTask('deploy', "Pushes new version to GAE platform.", [
        'build', 'shell', 'version', 'gae:update',
    ]);


    // Clean-Up (clean) //////////////////////////////////////////////////////

    grunt.task.loadNpmTasks('grunt-contrib-clean');
    config.clean = {build: 'build/*'};


    // File Copy (copy) //////////////////////////////////////////////////////

    grunt.task.loadNpmTasks('grunt-contrib-copy');
    config.copy = {
        api: {src: 'api/**/*.json', dest: 'build/'},  // minify later in-place
        favicon: {src: 'favicon.ico', dest: 'build/'},
        robots: {src: 'robots.txt', dest: 'build/'},
        unresolvedPy: {src: 'unresolved/__init__.py', dest: 'build/'},
    };


    // JSON Minification In-Place (json-minify) //////////////////////////////
    // n.b. unlike other minfication plug-ins, this one only works in-place //
    
    grunt.task.loadNpmTasks('grunt-json-minify');
    config['json-minify'] = {api: {files: 'build/api/**/*.json'}};


    // Stylesheet Copy and Minification (cssmin) /////////////////////////////

    grunt.task.loadNpmTasks('grunt-contrib-cssmin');
    config.cssmin = {
        options: {keepSpecialComments: 0},
        style: {files: {'build/style.css': 'style.css'}},
    };


    // HTML Generation from Mustache Templates (mustache_render) /////////////

    grunt.task.loadNpmTasks('grunt-mustache-render');
    config.mustache_render = {
        options: {clear_cache: doWatch, directory: 'partials/'},

        pages: {files: (function getMustachePages(nodes, base, up, home) {
            var results = [];
            var grandchildren = {};  // map of slugs to Mustache data object
            var last = null;

            if (!up) {
                home = up = {self: {href: '/', title: "Home"}, isHome: true};
                results.push({
                    template: 'pages/index.mustache',
                    dest: 'build/pages/index.html',
                    data: up,
                });
            }

            Object.keys(nodes).forEach(function (slug) {
                var node = nodes[slug];
                var href = base + '/' + slug;
                var fragment = 'pages' + href;
                var data = {
                    self: {href: href, title: node.title},
                    up: up.self,
                    home: home.self,
                    upEqHome: up === home,
                    isPage: true,
                };

                if (node.children) {
                    grandchildren[slug] = data;
                    results.push({
                        template: fragment + '/index.mustache',
                        dest: 'build/' + fragment + '/index.html',
                        data: data,
                    });
                } else {
                    results.push({
                        template: fragment + '.mustache',
                        dest: 'build/' + fragment + '.html',
                        data: data,
                    });
                }

                if (up.children) {
                    up.children.push(data.self);
                } else {
                    up.isParent = true;
                    up.children = [data.self];
                }

                if (last) {
                    data.prev = last.self;
                    last.next = data.self;
                }
                last = data;
            });

            return results.concat.apply(
                results,
                Object.keys(grandchildren).map(function (slug) {
                    return getMustachePages(nodes[slug].children,
                      base + '/' + slug, grandchildren[slug], home);
                })
            );
        }(SITEMAP, ''))},

        unresolvedError404: {files: [{
            template: 'unresolved/error404.mustache',
            dest: 'build/unresolved/error404.html',
            data: {self: {title: "Not Found"}, isDynamic: true},
        }]},

        unresolvedRedirect: {files: [{
            template: 'unresolved/redirect.mustache',
            dest: 'build/unresolved/redirect.html',
            data: {self: {title: "Moved Permanently"}, isDynamic: true},
        }]},
    };


    // HTML Minification In-Place (htmlmin) //////////////////////////////////
    // n.b. we run this one in-place in order to operate on mustache output //

    grunt.task.loadNpmTasks('grunt-contrib-htmlmin');
    config.htmlmin = {
        options: {collapseBooleanAttributes: true, collapseWhitespace: true,
          minifyCSS: true, minifyJS: true, removeAttributeQuotes: true,
          removeCDATASectionsFromCDATA: true, removeComments: true,
          removeCommentsFromCDATA: true, removeEmptyAttributes: true,
          removeEmptyElements: true, removeOptionalTags: true,
          removeRedundantAttributes: true, useShortDoctype: true},

        pages: {expand: true, cwd: 'build/', src: 'pages/**/*.html',
          dest: 'build/'},
        unresolvedError404: {expand: true, cwd: 'build/',
          src: 'unresolved/error404.html', dest: 'build/'},
        unresolvedRedirect: {expand: true, cwd: 'build/',
          src: 'unresolved/redirect.html', dest: 'build/'},
    };


    // app.yaml Builder Task (appyaml) ///////////////////////////////////////

    grunt.task.registerTask('appyaml', "Build app.yaml config.", function () {
        var MIME_HTML = 'text/html; charset=utf-8';

        var BASICS = {application: 'ankiatts', version: 'local',
          runtime: 'python27', api_version: '1', threadsafe: true,
          default_expiration: '12h'};

        var INDICES = ['/(', ')'].join((function getIndices(nodes) {
            return Object.keys(nodes).
                filter(function (slug) { return nodes[slug].children; }).
                map(function (slug) {
                    var opt = getIndices(nodes[slug].children);
                    return opt ? [slug, '(/(', opt, '))?'].join('') : slug;
                }).join('|');
        }(SITEMAP)));

        var LEAVES = ['/(', ')'].join((function getLeaves(nodes) {
            return Object.keys(nodes).map(function (slug) {
                var children = nodes[slug].children;
                return children ?
                    [slug, ['(', ')'].join(getLeaves(children))].join('/') :
                    slug;
            }).join('|');
        }(SITEMAP)));

        var HANDLERS = [
            {url: '/', static_files: 'pages/index.html',
              upload: 'pages/index\\.html', mime_type: MIME_HTML},
            {url: INDICES, static_files: 'pages/\\1/index.html',
              upload: ['pages', INDICES, '/index\\.html'].join(''),
              mime_type: MIME_HTML},
            {url: LEAVES, static_files: 'pages/\\1.html',
              upload: ['pages', LEAVES, '\\.html'].join(''),
              mime_type: MIME_HTML},

            {url: '/style\\.css', static_files: 'style.css',
              upload: 'style\\.css'},
            {url: '/favicon\\.ico', static_files: 'favicon.ico',
              upload: 'favicon\\.ico', expiration: '35d'},
            {url: '/robots\\.txt', static_files: 'robots.txt',
              upload: 'robots\\.txt', expiration: '35d'},

            // TODO always-changing /api/update/xxx URLs; initially...
            //      /api/update/abc123-1.0.0     => good-version.json
            //      /api/update/abc123-1.0.0-dev => need-newer.json
            //      /api/update/abc123-1.0.0-pre => need-newer.json

            {url: '/api/update/[a-z\\d]+-\\d+\\.\\d+\\.\\d+-(dev|pre)',
              static_files: 'api/update/unreleased.json',
              upload: 'api/update/unreleased\\.json'},

            {url: '/api/update', static_files: 'api/update/index.json',
              upload: 'api/update/index\\.json', expiration: '35d'},
            {url: '/api', static_files: 'api/index.json',
              upload: 'api/index\\.json', expiration: '35d'},

            {url: '/[aA][pP][iI](/.*)?', script: 'unresolved.api'},
            {url: '.*', script: 'unresolved.other'},
        ];

        var FORCE = {secure: 'always'};

        grunt.file.write(
            'build/app.yaml',

            Array.prototype.concat(
                Object.keys(BASICS).map(function (key) {
                    return [key, BASICS[key]].join(': ');
                }),
                '',
                'handlers:',
                HANDLERS.map(function (properties) {
                    Object.keys(FORCE).forEach(function (key) {
                        properties[key] = FORCE[key];
                    });

                    return ['- ', '\n'].join(
                        Object.keys(properties).map(function (key) {
                            return [key, properties[key]].join(': ');
                        }).join('\n  ')
                    );
                })
            ).join('\n')
        );
    });


    // Git Environment Queries (shell) ///////////////////////////////////////

    grunt.task.loadNpmTasks('grunt-shell');
    config.shell = {
        branch: {
            command: 'git symbolic-ref --short HEAD',
            options: {
                callback: function (error, stdout, stderr, next) {
                    stdout = stdout && stdout.trim && stdout.trim();

                    if (error || !stdout || stderr) {
                        if (
                            stderr && stderr.indexOf &&
                            stderr.indexOf('HEAD is not a symbolic') > -1
                        ) {
                            grunt.option('git.branch', 'detached');
                            grunt.log.error("In detached HEAD state");
                            next();
                        } else {
                            next(false);
                        }
                    } else {
                        grunt.option('git.branch', stdout);
                        grunt.log.ok("Current branch is " + stdout);
                        next();
                    }
                },
            },
        },

        tag: {
            command: 'git describe --candidates=0 --tags',
            options: {
                callback: function (error, stdout, stderr, next) {
                    stdout = stdout && stdout.trim && stdout.trim();

                    if (error || !stdout || stderr) {
                        if (
                            stderr && stderr.indexOf &&
                            stderr.indexOf('no tag exactly matches') > -1
                        ) {
                            grunt.option('git.tag', null);
                            grunt.log.error("No tag for this revision");
                            next();
                        } else {
                            next(false);
                        }
                    } else {
                        grunt.option('git.tag', stdout);
                        grunt.log.ok("Current tag is " + stdout);
                        next();
                    }
                },
            },
        },

        revision: {
            command: 'git rev-parse --short --verify HEAD',
            options: {
                callback: function (error, stdout, stderr, next) {
                    stdout = stdout && stdout.trim && stdout.trim();

                    if (error || !stdout || stderr) {
                        next(false);
                    } else {
                        grunt.option('git.revision', stdout);
                        grunt.log.ok("Current revision is " + stdout);
                        next();
                    }
                },
            },
        },

        dirty: {
            command: 'git status --porcelain',
            options: {
                callback: function (error, stdout, stderr, next) {
                    if (error || stderr) {
                        next(false);
                    } else {
                        stdout = stdout && stdout.trim && stdout.trim();

                        if (stdout === '') {
                            grunt.option('git.dirty', false);
                            grunt.log.ok("Working tree is clean");
                        } else {
                            grunt.option('git.dirty', true);
                            grunt.log.error("Working tree is dirty");
                        }

                        next();
                    }
                },
            },
        },
    };


    // Set Deployment Version (version) //////////////////////////////////////

    grunt.task.registerTask('version', "Set GAE version.", function () {
        this.requires('shell');

        var version = ['git.branch', 'git.tag', 'git.revision'].
            map(grunt.option).
            filter(Boolean).
            map(function (component) {
                return component.toString().toLowerCase().
                    replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            }).
            filter(Boolean).
            join('-');

        var DIRTY = '-dirty';
        var MAX_LEN = 50;
        version = grunt.option('git.dirty') ?
            version.substr(0, MAX_LEN - DIRTY.length) + DIRTY :
            version.substr(0, MAX_LEN);

        grunt.option('version', version);
        grunt.log.ok("GAE deployment version is " + version);
    });


    // Google App Engine (gae) Runner and Updater ////////////////////////////

    grunt.task.loadNpmTasks('grunt-gae');
    config.gae = {
        options: {path: 'build/'},
        run: {action: 'run', options: {async: doWatch}},
        update: {
            action: 'update',
            options: { version: '<%= grunt.option("version") || "test" %>', },
        },
    };


    // Watcher (watch) ///////////////////////////////////////////////////////

    grunt.task.loadNpmTasks('grunt-contrib-watch');
    config.watch = {
        options: {spawn: false},  // required for grunt.event.on logic to work

        grunt: {files: ['Gruntfile.js', 'sitemap.json'], tasks: 'build',
          options: {reload: true}},

        favicon: {files: 'favicon.ico', tasks: 'copy:favicon'},
        robots: {files: 'robots.txt', tasks: 'copy:robots'},
        unresolvedPy: {files: 'unresolved/__init__.py',
          tasks: 'copy:unresolvedPy'},

        api: {files: 'api/**/*.json', tasks: ['copy:api', 'json-minify:api']},

        style: {files: 'style.css', tasks: ['cssmin:style']},

        pages: {files: 'pages/**/*.mustache',
          tasks: ['mustache_render:pages', 'htmlmin:pages']},

        // these re-copy the "unresolved" module so its cached HTML is cleared
        partials: {files: 'partials/*.mustache',
          tasks: [
            'mustache_render:pages',
            'mustache_render:unresolvedError404',
            'mustache_render:unresolvedRedirect',
            'htmlmin:pages',
            'htmlmin:unresolvedError404',
            'htmlmin:unresolvedRedirect',
            'copy:unresolvedPy',
          ]},
        unresolvedError404: {files: 'unresolved/error404.mustache',
          tasks: [
            'mustache_render:unresolvedError404',
            'htmlmin:unresolvedError404',
            'copy:unresolvedPy',
          ]},
        unresolvedRedirect: {files: 'unresolved/redirect.mustache',
          tasks: [
            'mustache_render:unresolvedRedirect',
            'htmlmin:unresolvedRedirect',
            'copy:unresolvedPy',
          ]},
    };

    (function () {
        var OLD_VALUES = {};
        ['copy.api.src', 'json-minify.api.files',
          'mustache_render.pages.files', 'htmlmin.pages.src'].
            forEach(function (key) { OLD_VALUES[key] = grunt.config(key); });

        grunt.event.on('watch', function (action, path, target) {
            // n.b. doing a reset here preps any task that has had its
            // configuration clobbered by a related task (e.g. watch:pages
            // clobbers the mustache_render.pages.files list, but if
            // watch:partials kicks off, then that full list needs to be
            // in-place to rebuild all pages).
            Object.keys(OLD_VALUES).forEach(function (key) {
                grunt.config(key, OLD_VALUES[key]);
            });

            if (action === 'changed' || action === 'added') {
                switch (target) {
                    case 'api':
                        grunt.config('copy.api.src', path);
                        grunt.config('json-minify.api.files', 'build/' + path);
                        break;

                    case 'pages':
                        grunt.config(
                            'mustache_render.pages.files',
                            OLD_VALUES['mustache_render.pages.files'].
                                filter(function (file) {
                                    return file.template === path;
                                })
                        );
                        grunt.config(
                            'htmlmin.pages.src',
                            path.replace(/\.mustache$/, '.html')
                        );
                        break;
                }
            } else {
                grunt.fail.fatal(action + " not supported; please reload");
                process.exit();
            }
        });
    }());
};
