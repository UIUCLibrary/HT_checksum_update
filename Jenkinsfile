@Library("ds-utils")
import org.ds.*
@Library(["devpi", "PythonHelpers"]) _

SUPPORTED_LINUX_VERSIONS = ['3.6', '3.7', '3.8']
SUPPORTED_WINDOWS_VERSIONS = ['3.6', '3.7', '3.8']


def getDevPiStagingIndex(){

    if (env.TAG_NAME?.trim()){
        return "tag_staging"
    } else{
        return "${env.BRANCH_NAME}_staging"
    }
}

DEVPI_CONFIG = [
    index: getDevPiStagingIndex(),
    server: 'https://devpi.library.illinois.edu',
    credentialsId: 'DS_devpi',
]


def startup(){
    stage("Getting Distribution Info"){
        node('linux && docker') {
            ws{
                checkout scm
                try{
                    docker.image('python').inside {
                        timeout(2){
                            withEnv(['PIP_NO_CACHE_DIR=off']) {
                                sh(
                                   label: "Running setup.py with dist_info",
                                   script: """python --version
                                              python setup.py dist_info
                                           """
                                )
                            }
                            stash includes: "*.dist-info/**", name: 'DIST-INFO'
                            archiveArtifacts artifacts: "*.dist-info/**"
                        }
                    }
                } finally{
                    cleanWs(
                        deleteDirs: true,
                        patterns: [
                            [pattern: "*.dist-info/", type: 'INCLUDE'],
                            [pattern: "**/__pycache__", type: 'INCLUDE'],
                        ]
                    )
                }
            }
        }
    }
}

def get_props(){
    stage("Reading Package Metadata"){
        node() {
            try{
                unstash "DIST-INFO"
                def metadataFile = findFiles(excludes: '', glob: '*.dist-info/METADATA')[0]
                def package_metadata = readProperties interpolate: true, file: metadataFile.path
                echo """Metadata:

    Name      ${package_metadata.Name}
    Version   ${package_metadata.Version}
    """
                return package_metadata
            } finally {
                cleanWs(
                    patterns: [
                            [pattern: '*.dist-info/**', type: 'INCLUDE'],
                        ],
                    notFailBuild: true,
                    deleteDirs: true
                )
            }
        }
    }
}

startup()
props = get_props()

pipeline {
    agent none

    options {
        buildDiscarder logRotator(artifactDaysToKeepStr: '30', artifactNumToKeepStr: '30', daysToKeepStr: '100', numToKeepStr: '100')
    }
    parameters {
        string(name: "PROJECT_NAME", defaultValue: "HathiTrust Checksum Updater", description: "Name given to the project")
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
        booleanParam(name: 'TEST_RUN_TOX', defaultValue: false, description: 'Run Tox Tests')
        booleanParam(name: "PACKAGE_CX_FREEZE", defaultValue: false, description: "Create a package with CX_Freeze")
        booleanParam(name: "DEPLOY_SCCM", defaultValue: false, description: "Create SCCM deployment package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to production devpi on https://devpi.library.illinois.edu/production/release. Release Branch Only")
        booleanParam(name: "UPDATE_DOCS", defaultValue: false, description: "Update online documentation")
        string(name: 'URL_SUBFOLDER', defaultValue: "hathi_checksum_updater", description: 'The directory that the docs should be saved under')
    }
    stages {
        stage("Getting Distribution Info"){
           agent {
                dockerfile {
                    filename 'ci/docker/python/linux/jenkins/Dockerfile'
                    label 'linux && docker'
                }
            }

            steps{
                sh "python setup.py dist_info"
            }
            post{
                success{
                    stash includes: "HathiChecksumUpdater.dist-info/**", name: 'DIST-INFO'
                    archiveArtifacts artifacts: "HathiChecksumUpdater.dist-info/**"
                }
            }
        }
        stage("Building") {

            stages{
                stage("Python Package"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    steps {
                        timeout(5){
                            sh(
                               label: "Building Python Package",
                               script:'''mkdir -p logs
                                         python setup.py build -b build'''
                            )
                        }
                    }
                }
                stage("Sphinx Documentation"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    steps{
                        timeout(5){
                            sh(
                               label: "Building docs",
                               script: '''mkdir -p logs
                               python -m sphinx docs/source build/docs/html -d build/docs/.doctrees -w logs/build_sphinx.log -c docs/source
                                '''
                            )
                        }
                    }
                    post{
                        always {
                            archiveArtifacts artifacts: "logs/build_sphinx.log"
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log')])
                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                def DOC_ZIP_FILENAME = "${props.Name}-${props.Version}.doc.zip"
                                zip archive: true, dir: "build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                                stash includes: "dist/${DOC_ZIP_FILENAME},build/docs/html/**", name: 'DOCS_ARCHIVE'
                            }
                        }
                    }
                }

            }
        }
        stage("Tests") {
            when{
                equals expected: true, actual: params.RUN_CHECKS
            }
            stages{
                stage('Code Quality'){
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    stages{
                        stage("Run Tests"){
                            parallel {
                                stage("Run Pytest Unit Tests"){
                                    environment{
                                        junit_filename = "junit-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                                    }

                                    steps{
                                        timeout(5){
                                            catchError(buildResult: "UNSTABLE", message: 'pytest found issues', stageResult: "UNSTABLE") {
                                                sh(
                                                   label: "Running pytest",
                                                   script: """mkdir -p reports/coverage
                                                              pytest --junitxml=reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:reports/coverage/ --cov=hathi_checksum
                                                              """
                                                )
                                            }
                                        }
                                    }
                                    post {
                                        always {
                                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/coverage', reportFiles: 'index.html', reportName: 'Coverage', reportTitles: ''])
                                            junit "reports/pytest/${env.junit_filename}"
                                        }
                                    }
                                }
                                stage("Run Flake8 Static Analysis") {
                                    steps{
                                        catchError(buildResult: "SUCCESS", message: 'flake8 found issues', stageResult: "UNSTABLE") {
                                            sh(
                                                label: "Running flake8",
                                                script: """mkdir -p logs
                                                           flake8 hathi_checksum --tee --output-file=logs/flake8.log
                                                           """
                                            )
                                        }
                                    }
                                    post {
                                        always {
                                            recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                        }
                                    }
                                }
                                stage("DocTest"){
                                    steps{
                                        timeout(5){
                                            catchError(buildResult: "SUCCESS", message: 'Doctest found issues', stageResult: "UNSTABLE") {
                                                sh(
                                                    label: "Running Doctest",
                                                    script: """mkdir -p logs
                                                               python -m sphinx -b doctest docs/source build/docs -d build/docs/.doctrees -w logs/doctest.log -c docs/source
                                                               """
                                                )
                                            }
                                        }
                                    }
                                    post{
                                        always {
                                            archiveArtifacts artifacts: 'logs/doctest.log'
                                            recordIssues(tools: [sphinxBuild(id: 'Doctest', name: 'DocTest', pattern: 'logs/doctest.log')])
                                        }
                                    }
                                }
                                stage("MyPy"){
                                    steps{
                                        timeout(5){
                                            catchError(buildResult: "SUCCESS", message: 'MyPy found issues', stageResult: "UNSTABLE") {
                                                sh (script: '''mkdir -p logs
                                                               mkdir -p reports/mypy_html
                                                               mypy -p hathi_checksum --html-report reports/mypy_html | tee logs/mypy.log
                                                '''
                                                )
                                            }
                                        }
                                    }
                                    post{
                                        always {
                                            recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy_html', reportFiles: 'index.html', reportName: 'MyPy', reportTitles: ''])
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                stage('Run Tox'){
                    when{
                        equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    steps {
                        echo "Running tox tests"
                        script{
                            def tox
                            node(){
                                checkout scm
                                tox = load('ci/jenkins/scripts/tox.groovy')
                            }
                            def windowsJobs = [:]
                            def linuxJobs = [:]
                            stage("Scanning Tox Environments"){
                                parallel(
                                    'Linux':{
                                        linuxJobs = tox.getToxTestsParallel(
                                                envNamePrefix: 'Tox Linux',
                                                label: 'linux && docker',
                                                dockerfile: 'ci/docker/python/linux/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            )
                                    },
                                    'Windows':{
                                        windowsJobs = tox.getToxTestsParallel(
                                                envNamePrefix: 'Tox Windows',
                                                label: 'windows && docker',
                                                dockerfile: 'ci/docker/python/windows/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                         )
                                    },
                                    failFast: true
                                )
                            }
                            parallel(windowsJobs + linuxJobs)
                        }
                    }
                }
            }
        }
        stage("Packaging") {

            parallel {
                stage("Source and Wheel formats"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    steps{
                        timeout(5){
                            sh "python setup.py sdist -d dist bdist_wheel -d dist"
                        }
                        stash includes: 'dist/*.whl', name: "whl"
                        stash includes: 'dist/*.zip,dist/*.tar.gz', name: "sdist"

                    }
                    post{
                        success{
                            archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                        }
                    }
                }
                stage("Windows CX_Freeze MSI"){
                    when{
                        equals expected: true, actual: params.PACKAGE_CX_FREEZE
                        beforeAgent true
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/windows/jenkins/Dockerfile'
                            label "windows && docker"
                        }
                    }
                    steps{
                        timeout(10){
                            bat(
                                label: "Freezing to msi installer",
                                script:"python cx_setup.py bdist_msi --add-to-path=true -k --bdist-dir build/msi -d dist"
                                )
                        }


                    }
                    post{
                        success{
                            dir("dist") {
                                stash includes: "*.msi", name: "msi"
                            }
                            archiveArtifacts artifacts: "dist/*.msi", fingerprint: true
                        }
                    }
                }
            }
        }
        stage("Deploy to DevPi") {
            when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
                beforeAgent true
                beforeOptions true
            }
            options{
                timestamps()
                lock("hathi_checksum-devpi")
            }
            stages{
                stage("Deploy to Devpi Staging") {
                    agent {
                        dockerfile {
                            filename 'ci/docker/python/linux/tox/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                        }
                    }
                    steps {
                        unstash "sdist"
                        unstash "whl"
                        unstash "DOCS_ARCHIVE"
                        script{
                            def devpi = load('ci/jenkins/scripts/devpi.groovy')
                            devpi.upload(
                                server: DEVPI_CONFIG.server,
                                credentialsId: DEVPI_CONFIG.credentialsId,
                                index: getDevPiStagingIndex(),
                                clientDir: './devpi'
                            )
                        }
                    }
                }
                stage("Test DevPi Package") {
                    steps{
                        script{
                            def devpi
                            node(){
                                checkout scm
                                devpi = load('ci/jenkins/scripts/devpi.groovy')
                            }
                            linuxPackages = [:]
                            SUPPORTED_LINUX_VERSIONS.each{pythonVersion ->
                                linuxPackages["Test Python ${pythonVersion}: sdist Linux"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/python/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                                                label: 'linux && docker'
                                            ]
                                        ],
                                        devpi: DEVPI_CONFIG,
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'tar.gz'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                                linuxPackages["Test Python ${pythonVersion}: wheel Linux"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/python/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                                                label: 'linux && docker'
                                            ]
                                        ],
                                        devpi: DEVPI_CONFIG,
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'whl'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                            }
                            def windowsPackages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{pythonVersion ->
                                windowsPackages["Test Python ${pythonVersion}: sdist Windows"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/python/windows/tox/Dockerfile',
                                                additionalBuildArgs: "--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE",
                                                label: 'windows && docker'
                                            ]
                                        ],
                                        devpi: DEVPI_CONFIG,
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'tar.gz'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                                windowsPackages["Test Python ${pythonVersion}: wheel Windows"] = {
                                    devpi.testDevpiPackage(
                                        agent: [
                                            dockerfile: [
                                                filename: 'ci/docker/python/windows/tox/Dockerfile',
                                                additionalBuildArgs: "--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE",
                                                label: 'windows && docker'
                                            ]
                                        ],
                                        devpi: DEVPI_CONFIG,
                                        package:[
                                            name: props.Name,
                                            version: props.Version,
                                            selector: 'whl'
                                        ],
                                        test:[
                                            toxEnv: "py${pythonVersion}".replace('.',''),
                                        ]
                                    )
                                }
                            }
                            parallel(windowsPackages + linuxPackages)
                        }
                    }
                }
            }
            post{
                success{
                    node('linux && docker') {
                        script{
                            if (!env.TAG_NAME?.trim()){
                                checkout scm
                                def devpi = load('ci/jenkins/scripts/devpi.groovy')
                                docker.build("uiucpresconpackager:devpi",'-f ./ci/docker/python/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                    devpi.pushPackageToIndex(
                                        pkgName: props.Name,
                                        pkgVersion: props.Version,
                                        server: DEVPI_CONFIG.server,
                                        indexSource: "DS_Jenkins/${getDevPiStagingIndex()}",
                                        indexDestination: "DS_Jenkins/${env.BRANCH_NAME}",
                                        credentialsId: DEVPI_CONFIG.credentialsId
                                    )
                                }
                            }
                       }
                    }
                }
                cleanup{
                    node('linux && docker') {
                       script{
                            checkout scm
                            def devpi = load('ci/jenkins/scripts/devpi.groovy')
                            docker.build("uiucpresconpackager:devpi",'-f ./ci/docker/python/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                devpi.removePackage(
                                    pkgName: props.Name,
                                    pkgVersion: props.Version,
                                    index: "DS_Jenkins/${getDevPiStagingIndex()}",
                                    server: DEVPI_CONFIG.server,
                                    credentialsId: DEVPI_CONFIG.credentialsId
                                )
                            }
                       }
                    }
                }
            }
        }
        stage("Deployment"){
            parallel{

                stage("Deploy - SCCM"){
                    agent any
                    when {
                        equals expected: true, actual: params.DEPLOY_SCCM
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    stages{
                        stage("Deploy - Staging") {



                            steps {
                                deployStash("msi", "${env.SCCM_STAGING_FOLDER}/${params.PROJECT_NAME}/")
                                input("Deploy to production?")
                            }
                        }

                        stage("Deploy - SCCM upload") {

                            steps {
                                deployStash("msi", "${env.SCCM_UPLOAD_FOLDER}")
                            }
                        }
                        stage("Creating Deployment request"){
                            steps{
                                script{
                                    unstash "Source"
                                    def  deployment_request = requestDeploy this, "deployment.yml"
                                    echo deployment_request
                                    writeFile file: "deployment_request.txt", text: deployment_request
                                    archiveArtifacts artifacts: "deployment_request.txt"
                                }
                            }
                        }
                    }
                }
                stage("Documentation Deployment"){
                    agent any
                    when {
                        equals expected: true, actual: params.UPDATE_DOCS
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    stages{
                        stage("Update online documentation") {
                            options{
                               timeout(5)  // Timeout after 5 minutes. This shouldn't take this long but it hangs for some reason
                            }
                            steps {
                                dir("build/docs/html/"){
                                    bat "dir /s /B"
                                    sshPublisher(
                                        publishers: [
                                            sshPublisherDesc(
                                                configName: 'apache-ns - lib-dccuser-updater',
                                                sshLabel: [label: 'Linux'],
                                                transfers: [sshTransfer(excludes: '',
                                                execCommand: '',
                                                execTimeout: 120000,
                                                flatten: false,
                                                makeEmptyDirs: false,
                                                noDefaultExcludes: false,
                                                patternSeparator: '[, ]+',
                                                remoteDirectory: "${params.URL_SUBFOLDER}",
                                                remoteDirectorySDF: false,
                                                removePrefix: '',
                                                sourceFiles: '**')],
                                            usePromotionTimestamp: false,
                                            useWorkspaceInPromotion: false,
                                            verbose: true
                                            )
                                        ]
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
