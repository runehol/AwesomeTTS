/**
 * Gruntfile for AwesomeTTS web
 *
 * Includes tasks for automatically testing minified code (`grunt run`) and
 * deploying up to Google App Engine (`grunt deploy`).
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
        'deploy',
        "Minify static files and deploy to GAE w/ a git-derived app version.",
        [
            'clean:build',
            'copy:build',
            'cssmin:build',
            'htmlmin:build',
            'json-minify:build',
            'shell:branch',
            'shell:dirty',
            'robotless',
            'gae:deploy',
        ]
    );

    grunt.registerTask(
        'run',
        "Minify static files and run the GAE SDK test server.",
        [
            'clean:build',
            'copy:build',
            'cssmin:build',
            'htmlmin:build',
            'json-minify:build',
            'gae:run',
        ]
    );

    var isStable = function () {
        return grunt.option('branch') === 'stable' &&
            grunt.option('dirty') === false;
    };

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
                            next(false);
                        } else {
                            grunt.option('branch', stdout);
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
                            if (
                                typeof stdout === 'string' &&
                                stdout.trim() === ''
                            ) {
                                grunt.option('dirty', false);
                                grunt.log.ok("Working tree is clean");
                            } else {
                                grunt.option('dirty', true);
                                grunt.log.error("Working tree is dirty");
                            }

                            next();
                        }
                    },
                },
            },
        },

        gae: {
            options: {
                path: 'build/',
            },

            deploy: {
                action: 'update',
                options: {
                    version: isStable() ? 'stable' : 'test',
                },
            },

            run: {
                action: 'run',
            },
        },
    });

    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-contrib-htmlmin');
    grunt.loadNpmTasks('grunt-gae');
    grunt.loadNpmTasks('grunt-json-minify');
    grunt.loadNpmTasks('grunt-shell');

    grunt.registerTask(
        'robotless',
        "For non-stable deployments, set robots file to be exclude-all.",
        function () {
            if (isStable()) {
                grunt.log.ok("Stable deploy; retaining robots.txt");
            } else {
                grunt.log.error("Test deploy; zapping robots.txt");
                grunt.file.write(
                    'build/robots.txt',
                    "User-agent: *\nDisallow: /\n"
                );
            }
        }
    );
};
