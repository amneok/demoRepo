pipeline {
  agent any
  stages {
    stage('Commit') {
      steps {
        sh '''#!/bin/bash -xe

echo ${env.BUILD_ID}'''
      }
    }
    stage('Acceptance') {
      steps {
        sh '''#!/bin/bash -xe

echo "Bravo2"'''
      }
    }
    stage('Performance') {
      steps {
        sh '''#!/bin/bash -xe

echo "Testing load"'''
      }
    }
    stage('Promote') {
      steps {
        sh '''#!/bin/bash -xe

echo "Promoting"'''
      }
    }
  }
}
