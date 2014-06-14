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
 * and deploying it to Google App Engine with a git-derived version.
 */

/*jslint indent:4*/
/*jslint node:true*/
/*jslint regexp:true*/

module.exports = function (grunt) {
    'use strict';


    // Task Aliases //////////////////////////////////////////////////////////

    grunt.task.registerTask('default', 'help');

    grunt.task.registerTask('help', "Display usage and tasks.", function() {
        grunt.help.display();
    });

    grunt.task.registerTask('build', "Build all into build subdirectory.", [
        'clean:build', 'copy:build', 'cssmin:build', 'htmlmin:build',
        'json-minify:build',
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
                    'app.yaml',
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
                removeEmptyElements: true,
                removeOptionalTags: true,
                removeRedundantAttributes: true,
                useShortDoctype: true,
            },

            build: {
                expand: true,
                src: [
                    'index.html',
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
            },

            update: {
                action: 'update',
                options: {
                    version: '<%= grunt.option("version") || "test" %>',
                },
            },
        },
    });


    // Task Implementations //////////////////////////////////////////////////

    [
        'grunt-contrib-clean', 'grunt-contrib-copy', 'grunt-contrib-cssmin',
        'grunt-contrib-htmlmin', 'grunt-json-minify', 'grunt-shell',
        'grunt-gae',
    ].forEach(grunt.task.loadNpmTasks);

    grunt.task.registerMultiTask('options', "Set option values.", function() {
        var value = typeof this.data === 'function' ? this.data() : this.data;
        grunt.option(this.target, value);
        grunt.log.ok([this.target, value || "set"].join(" now "));
    });
};
