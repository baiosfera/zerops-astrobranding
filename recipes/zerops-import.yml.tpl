# Full Project Import Template (for `zcli project project-import`)
# Note: For importing into an existing ZCP project via `zerops_import`, use
# `recipes/zerops-core-cluster.yaml` (omits project.name/corePackage and zcp/localstorage).
project:
  name: ${PROJECT_NAME}
  corePackage: ${CORE_PACKAGE}
  vault:
    PROJECT_NAME: ${PROJECT_NAME}
    FREEAPI_ENCRYPTION_KEY:
      value: <@generateRandomString(<64>)>
      sensitive: true
    FREELLMAPI_CLIENT_KEY:
      value: <@generateRandomString(<32>)>
      sensitive: true
    BIFROST_MASTER_VK:
      value: <@generateRandomString(<32>)>
      sensitive: true
    BIFROST_ADMIN_USERNAME:
      value: admin
    BIFROST_ADMIN_PASSWORD:
      value: <@generateRandomString(<20>)>Aa1!
      sensitive: true
    DEEPSEEK_API_KEY:
      value: ${DEEPSEEK_API_KEY}
      sensitive: true
    PAPERCLIP_BETTER_AUTH_SECRET:
      value: <@generateRandomString(<32>)>
      sensitive: true
    PAPERCLIP_SIGNING_SECRET:
      value: <@generateRandomString(<32>)>
      sensitive: true

services:
  - hostname: database
    type: postgresql:${DB_MODE}@18
    profile: oltp-hobby
    priority: 10

  - hostname: valkey
    type: valkey:${VALKEY_MODE}@7.2
    profile: hobby
    priority: 10

  - hostname: nats
    type: nats:single@2.12
    priority: 10

  - hostname: localstorage
    type: local-storage:single@1
    priority: 10

  - hostname: freellmapi
    type: ubuntu/nodejs@24
    buildFromGit: https://github.com/baiosfera/runtime-freellmapi
    enableSubdomainAccess: true
    priority: 8
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.25
      minFreeRamPercent: 10

  - hostname: bifrost
    type: alpine/go@1.22
    buildFromGit: https://github.com/baiosfera/runtime-bifrost
    enableSubdomainAccess: true
    priority: 6
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.25
      minFreeRamPercent: 10

  - hostname: hermes
    type: ubuntu/python@3.12
    buildFromGit: https://github.com/baiosfera/runtime-hermes
    enableSubdomainAccess: true
    priority: 4
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.5
      minFreeRamPercent: 10

  - hostname: pidev
    type: ubuntu/nodejs@26
    buildFromGit: https://github.com/baiosfera/runtime-pidev
    enableSubdomainAccess: true
    priority: 4
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.25
      minFreeRamPercent: 10

  - hostname: paperclip
    type: ubuntu/nodejs@26
    buildFromGit: https://github.com/baiosfera/runtime-paperclip
    enableSubdomainAccess: true
    priority: 4
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.5
      minFreeRamPercent: 10
