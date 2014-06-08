/**
 * Gruntfile for AwesomeTTS web
 *
 * Provides Grunt tasks for building the project, running it locally,
 * and deploying it to Google App Engine as either a "stable" or "unstable"
 * package.
 */

/*jslint indent:4*/
/*jslint node:true*/
/*jslint regexp:true*/

module.exports = function (grunt) {
    'use strict';

    grunt.registerTask('default', 'help');

    grunt.registerTask(
        'help',
        "Display usage, options, and available tasks.",
        function () {
            grunt.help.display();
        }
    );

    grunt.registerTask(
        'build',
        "Build the project into the build subdirectory.",
        [
            'clean:build',
            'copy:build',
            'cssmin:build',
            'htmlmin:build',
            'json-minify:build',
        ]
    );

    grunt.registerTask(
        'deploy',
        "Deploys a stable version of the project to Google App Engine.",
        [
            'shell:branch',
            'shell:dirty',
            'build',
            'robotstxt:allow',
            'gae:stable',
        ]
    );

    grunt.registerTask(
        'local',
        "Runs the project locally using Google App Engine SDK test server.",
        [
            'build',
            'robotstxt:allow',
            'gae:local',
        ]
    );

    grunt.registerTask(
        'remote',
        "Sends the project to Google App Engine for testing remotely.",
        [
            'build',
            'robotstxt:deny',
            'gae:test',
        ]
    );

    grunt.config.init({
        pkg: grunt.file.readJSON('package.json'),

        shell: {
            branch: {
                command: 'git symbolic-ref --short HEAD',
                options: {
                    callback: function (error, stdout, stderr, next) {
                        stdout = stdout && stdout.trim && stdout.trim();

                        if (error || !stdout || stderr) {
                            next(false);
                        } else if (stdout === 'stable') {
                            next();
                        } else {
                            grunt.log.fail("Not on the stable branch");
                            next(false);
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
                        } else if (stdout.trim() === '') {
                            next();
                        } else {
                            grunt.log.fail("Working tree is dirty");
                            next(false);
                        }
                    },
                },
            },
        },

        clean: {
            build: 'build/',
        },

        copy: {
            build: {
                src: [
                    'app.yaml',
                    'favicon.ico',
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

        robotstxt: {
            allow: {
                dest: 'build/',
                policy: [
                    {ua: '*', disallow: [
                        '/api',
                    ]},
                ],
            },

            deny: {
                dest: 'build/',
                policy: [
                    {ua: '*', disallow: '/'},
                ],
            },
        },

        gae: {
            options: {
                path: 'build/',
            },

            local: {
                action: 'run',
            },

            stable: {
                action: 'update',
                options: {
                    version: 'stable',
                },
            },

            test: {
                action: 'update',
                options: {
                    version: 'test',
                },
            },
        },
    });

    grunt.loadNpmTasks('grunt-shell');
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-contrib-htmlmin');
    grunt.loadNpmTasks('grunt-json-minify');
    grunt.loadNpmTasks('grunt-robots-txt');
    grunt.loadNpmTasks('grunt-gae');
};
