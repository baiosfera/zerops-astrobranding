project:
  name: ${PROJECT_NAME}
  corePackage: ${CORE_PACKAGE}

services:
  - hostname: database
    type: postgresql:${DB_MODE}@18

  - hostname: valkey
    type: valkey:${VALKEY_MODE}@7.2

  - hostname: nats
    type: nats:single@2.12

  - hostname: localstorage
    type: local-storage:single@1

  - hostname: freellmapi
    type: ubuntu/nodejs@24
    buildFromGit: https://github.com/baiosfera/runtime-freellmapi
    enableSubdomainAccess: true
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.25
      minFreeRamPercent: 10
    vault:
      FREEAPI_ENCRYPTION_KEY:
        value: <@generateRandomString(<64>)>
        sensitive: true

  - hostname: bifrost
    type: alpine/go@1.22
    buildFromGit: https://github.com/baiosfera/runtime-bifrost
    enableSubdomainAccess: true
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.25
      minFreeRamPercent: 10
    vault:
      BIFROST_MASTER_VK:
        value: <@generateRandomString(<32>)>
        sensitive: true

  - hostname: hermes
    type: ubuntu/python@3.12
    buildFromGit: https://github.com/baiosfera/runtime-hermes
    enableSubdomainAccess: true
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.5
      minFreeRamPercent: 10
    # Non-secret env vars (PROJECT_NAME, CREWAI_TELEMETRY_OPT_OUT) belong in runtime-hermes/zerops.yaml run.envVariables.

  - hostname: pidev
    type: ubuntu/nodejs@26
    buildFromGit: https://github.com/baiosfera/runtime-pidev
    enableSubdomainAccess: true
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.25
      minFreeRamPercent: 10
    vault:
      DEEPSEEK_API_KEY:
        value: ${DEEPSEEK_API_KEY}
        sensitive: true

  - hostname: paperclip
    type: ubuntu/nodejs@26
    buildFromGit: https://github.com/baiosfera/runtime-paperclip
    enableSubdomainAccess: true
    minContainers: 1
    maxContainers: 1
    verticalAutoscaling:
      cpuMode: SHARED
      minFreeRamGB: 0.5
      minFreeRamPercent: 10
    vault:
      PAPERCLIP_BETTER_AUTH_SECRET:
        value: <@generateRandomString(<32>)>
        sensitive: true
      PAPERCLIP_SIGNING_SECRET:
        value: <@generateRandomString(<32>)>
        sensitive: true
