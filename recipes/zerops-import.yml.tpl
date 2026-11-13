project:
  name: ${PROJECT_NAME}
  corePackage: ${CORE_PACKAGE}

services:
  - hostname: database
    type: postgresql@18
    mode: ${DB_MODE}

  - hostname: valkey
    type: valkey@7.2
    mode: ${VALKEY_MODE}

  - hostname: nats
    type: nats@2.12
    mode: NON_HA

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
    envSecrets:
      FREEAPI_ENCRYPTION_KEY: <@generateRandomString(<64>)>

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
    envSecrets:
      BIFROST_MASTER_VK: <@generateRandomString(<32>)>

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
    envVariables:
      PROJECT_NAME: ${PROJECT_NAME}
      CREWAI_TELEMETRY_OPT_OUT: "true"

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
    envVariables:
      PI_READ_ONLY: "false"
      DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY}

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
    envSecrets:
      PAPERCLIP_BETTER_AUTH_SECRET: <@generateRandomString(<32>)>
      PAPERCLIP_SIGNING_SECRET: <@generateRandomString(<32>)>
