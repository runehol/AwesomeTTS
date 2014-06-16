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
 *     $ grunt watch      # automatically rebuilds the project as needed with
 *                        # build activity output sent to the console
 *
 *     $ grunt run watch  # combines the above two, but the GAE SDK server is
 *                        # backgrounded, so only watch activity is visible
 *
 * The --live-reload flag can be used with build/run (to insert a livereload
 * script reference in the document) and/or watch (to activate the livereload
 * server).
 */

/*jslint indent:4*/
/*jslint node:true*/
/*jslint regexp:true*/

module.exports = function (grunt) {
    'use strict';

    var doDeploy = grunt.cli.tasks.indexOf('deploy') !== -1;
    var doWatch = grunt.cli.tasks.indexOf('watch') !== -1;
    var useLiveReload = !!grunt.option('live-reload');

    if (doDeploy && useLiveReload) {
        grunt.fail.fatal("Do not use --live-reload during deployment");
    }


    // Site Structure ////////////////////////////////////////////////////////

    var SITEMAP = {
        install: {title: "Installation"},

        services: {title: "Services", children: {
            ekho: {title: "Ekho"},
            espeak: {title: "eSpeak"},
            festival: {title: "Festival"},
            google: {title: "Google"},
            sapi5: {title: "Microsoft Speech API"},
            say: {title: "OS X Speech Synthesis"},
            yandex: {title: "Yandex.Translate"},
        }},

        usage: {title: "Usage", children: {
            'on-the-fly': {title: "Playing Audio On-the-Fly"},
            browser: {title: "Adding Audio via the Card Browser"},
            editor: {title: "Adding Audio via the Note Editor"},
        }},

        config: {title: "Configuration", children: {
            'on-the-fly': {title: "On-the-Fly and Keyboard Shortcuts"},
            text: {title: "Text Filtering and Cloze Handling"},
            mp3s: {title: "MP3 Generation and Throttling"},
            advanced: {title: "Advanced"},
        }},

        contribute: {title: "Contribute"},
    };


    // Task Aliases //////////////////////////////////////////////////////////

    grunt.task.registerTask('default', 'help');

    grunt.task.registerTask('help', "Display usage and tasks.", function() {
        grunt.help.display();
    });

    grunt.task.registerTask('build', "Build all into build subdirectory.", [
        'clean:build', 'copy:build', 'cssmin:build', 'mustache_render:build',
        'htmlmin:build', 'json-minify:build',
    ]);

    grunt.task.registerTask('run', "Runs project locally using GAE SDK.", [
        'build', 'gae:run',
    ]);

    grunt.task.registerTask('deploy', "Pushes new version to GAE platform.", [
        'build', 'shell:branch', 'shell:tag', 'shell:revision', 'shell:dirty',
        'options:version', 'gae:update',
    ]);


    // Task Configuration ////////////////////////////////////////////////////

    grunt.config.init({
        pkg: grunt.file.readJSON('package.json'),

        clean: {
            build: 'build/',
        },

        copy: {
            build: {
                src: [
                    'app.yaml',  // TODO break off and generate automatically
                    'favicon.ico',
                    'robots.txt',
                    'unresolved/*.py',
                    'api/**/*.json'  /* minified inline by json-minify */,
                ],
                dest: 'build/',
            },
        },

        cssmin: {
            options: {
                banner: null,
                keepSpecialComments: 0,
                report: 'min',
            },

            build: {
                files: {
                    'build/style.css': 'style.css',
                },
            },
        },

        mustache_render: {
            options: {
                clear_cache: false,
            },

            build: {
                options: {
                    directory: 'partials/',
                    prefix: '',
                    extension: '.mustache',
                    partial_finder: null,
                },

                files: Array.prototype.concat([
                    {
                        template: 'unresolved/error404.mustache',
                        dest: 'build/unresolved/error404.html',
                        data: {
                            title: "Not Found",
                            useLiveReload: useLiveReload,
                        },
                    },
                    {
                        template: 'unresolved/redirect.mustache',
                        dest: 'build/unresolved/redirect.html',
                        data: {title: "Moved Permanently"},
                    },
                ], (function getMustacheRenderFiles(nodes, base, up, home) {
                    var results = [];
                    var grandchildren = {};  // slugs to their parent's data
                    var last = null;

                    if (!up) {
                        home = up = {
                            self: {href: '/', title: "Home"},
                            useLiveReload: useLiveReload,
                        };
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
                            title: node.title,
                            self: {href: href, title: node.title},
                            up: up.self,
                            home: home.self,
                            useLiveReload: useLiveReload,
                            hasOrientation: true,
                            isUpAlsoHome: up === home,
                        };

                        if (
                            node.children &&
                            Object.keys(node.children).length
                        ) {
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
                            up.hasChildren = true;
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
                            return getMustacheRenderFiles(
                                nodes[slug].children,
                                base + '/' + slug,
                                grandchildren[slug],
                                home
                            );
                        })
                    );
                }(SITEMAP, ''))),
            },
        },

        htmlmin: {
            options: {
                caseSensitive: false,
                collapseBooleanAttributes: true,
                collapseWhitespace: true,
                conservativeCollapse: false,
                // ignoreCustomComments: [],
                keepClosingSlash: false,
                // lint: false,
                minifyCSS: true,
                minifyJS: true,
                // processScripts: [],
                removeAttributeQuotes: true,
                removeCDATASectionsFromCDATA: true,
                removeComments: true,
                removeCommentsFromCDATA: true,
                removeEmptyAttributes: true,
                removeEmptyElements: false /* true strips external scripts */,
                removeOptionalTags: true,
                removeRedundantAttributes: true,
                useShortDoctype: true,
            },

            build: {
                expand: true,
                cwd: 'build/',
                src: [
                    'pages/**/*.html',
                    'unresolved/*.html',
                ],
                dest: 'build/',
            },
        },

        'json-minify': {
            build: {
                files: 'build/api/**/*.json',
            },
        },

        shell: {
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
        },

        options: {
            version: function () {
                this.requires([
                    'shell:branch',
                    'shell:tag',
                    'shell:revision',
                    'shell:dirty',
                ]);

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

                return grunt.option('git.dirty') ?
                    version.substr(0, MAX_LEN - DIRTY.length) + DIRTY :
                    version.substr(0, MAX_LEN);
            },
        },

        gae: {
            options: {
                path: 'build/',
            },

            run: {
                action: 'run',
                options: {async: doWatch},
            },

            update: {
                action: 'update',
                options: {
                    version: '<%= grunt.option("version") || "test" %>',
                },
            },
        },

        watch: {
            options: {
                debounceDelay: 1000,
            },

            grunt: {
                files: 'Gruntfile.js',
                tasks: 'build',
            },

            raw: {
                files: [
                    'app.yaml',
                    'favicon.ico',
                    'robots.txt',
                    'unresolved/*.py',
                ],
                tasks: 'copy:build',
            },

            json: {
                files: 'api/**/*.json',
                tasks: ['copy:build', 'json-minify:build'],
            },

            mustache: {
                files: '{pages,partials,unresolved}/**/*.mustache',
                tasks: ['mustache_render:build', 'htmlmin:build'],
            },

            css: {
                files: 'style.css',
                tasks: 'cssmin:build',
            },

            livereload: useLiveReload ? {
                options: {livereload: true},
                files: 'build/**/*.{css,html}',
            } : {
                files: [],
                tasks: [],
            },
        },
    });


    // Task Implementations //////////////////////////////////////////////////

    [
        'grunt-contrib-clean', 'grunt-contrib-copy', 'grunt-contrib-cssmin',
        'grunt-mustache-render', 'grunt-contrib-htmlmin', 'grunt-json-minify',
        'grunt-shell', 'grunt-gae', 'grunt-contrib-watch',
    ].forEach(grunt.task.loadNpmTasks);

    grunt.task.registerMultiTask('options', "Set option values.", function() {
        var value = typeof this.data === 'function' ? this.data() : this.data;
        grunt.option(this.target, value);
        grunt.log.ok([this.target, value || "set"].join(" now "));
    });
};
