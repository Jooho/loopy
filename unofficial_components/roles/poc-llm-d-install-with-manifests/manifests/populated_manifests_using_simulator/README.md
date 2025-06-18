# LLM-D Manual Deployment


**Download required binaries**
This is just for PoC not related to LLMInferenceService
- yq
- kubectl or oc

**Pre-requirements**
- Install Gateway API/Gateway API extension CRD
	~~~
	kubectl $MODE -k https://github.com/llm-d/llm-d-inference-scheduler/deploy/components/crds-gateway-api
	kubectl $MODE -k https://github.com/llm-d/llm-d-inference-scheduler/deploy/components/crds-gie
	~~~
- Install istiod supporting gateway api extension feature (GATEWAY provider)
	~~~
	oc apply -k https://github.com/llm-d/llm-d-inference-scheduler/tree/main/deploy/components/istio-control-plane
	~~~

**KServe Perspective flow to deploy llmd type of llm inferenceService**
- Install KServe controller
- Create a new namespace "llmd-test-manual"
- Create LLMInferenceServiceConfig manifest
- Create LLMInferenceService manifest


**Detailed explanation of objects created behind the scenes.**
- Requirements
	~~~
	oc new-project llmd-test-manual

	export HF_TOKEN=XXX
	kubectl create secret generic llm-d-hf-token \
		--from-literal=HF_TOKEN="$HF_TEST_TOKEN"
	~~~

- Routing
	~~~
	# Set env
	export component=route
	
	# gateway created
	oc create -f ../populated_manifests/${component}/gateway.yaml
	
	# httpRoute created
	oc create -f ../populated_manifests/${component}/httproute.yaml
	
	# inferencePool created
	oc create -f ../populated_manifests/${component}/inferencePool.yaml
	
	# inferenceModel created
	oc create -f ../populated_manifests/${component}/inferenceModel.yaml
	~~~
- Distributed KVCache (exteral LMCache using redis)
	~~~
	# Set env
	export component=kvcache
	
	# serviceaccount for kvcache created
	oc create -f ../populated_manifests/${component}/sa.yaml
	
	# service created
	oc create -f ../populated_manifests/${component}/svc.yaml
	
	# configmap
	oc create -f ../populated_manifests/${component}/redis-configuration-configmap.yaml
	oc create -f ../populated_manifests/${component}/redis-health-configmap.yaml
	oc create -f ../populated_manifests/${component}/redis-script-configmap.yaml
	
	# kvcache pod created
	oc create -f ../populated_manifests/${component}/deployment.yaml
	~~~		
- Scheduler
	~~~
	# Set env
	export component=scheduler
	
	# serviceaccount for scheduler created
	oc create -f ../populated_manifests/${component}/sa.yaml
	
	# service created
	oc create -f ../populated_manifests/${component}/svc.yaml
	
	# role created
	oc create -f ../populated_manifests/${component}/role.yaml
	
	# rolebinding created
	oc create -f ../populated_manifests/${component}/rolebinding.yaml
	
	# destinationRule created
  oc create -f ../populated_manifests/${component}/rolebinding.yaml

	# deployment created
	oc create -f ../populated_manifests/${component}/deployment.yaml
	~~~		  				
- Decode
	~~~
	# Set env
	export component=decode
	
	# serviceaccount for scheduler created
	oc create -f ./${component}/sa.yaml
	
	# service created
	oc create -f ./${component}/svc.yaml
	
	# deployment created
	oc create -f ./${component}/deployment.yaml
	~~~		 		
- Prefill
	~~~
	# Set env
	export component=prefill
	
	# service created
	oc create -f ./${component}/svc.yaml
	
	# deployment created
	oc create -f ./${component}/deployment.yaml		
	~~~

**Test**
~~~
../../test-request.sh -n llmd-test-manual

namespace: %test_namespace%
Model ID:  none; will be discover from first entry in /v1/models

1 -> Fetching available models from the decode pod at 10.130.4.22…
Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "curl-5697" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "curl-5697" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "curl-5697" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "curl-5697" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
{"object":"list","data":[{"id":"meta-llama/Llama-3.2-3B-Instruct","object":"model","created":1749866136,"owned_by":"vllm","root":"meta-llama/Llama-3.2-3B-Instruct","parent":null,"max_model_len":65536,"permission":[{"id":"modelperm-0c0608d84793460e8cd9812fed5fc9a6","object":"model_permission","created":1749866136,"allow_create_engine":false,"allow_sampling":true,"allow_logprobs":true,"allow_search_indices":false,"allow_view":true,"allow_fine_tuning":false,"organization":"*","group":null,"is_blocking":false}]}]}pod "curl-5697" deleted

Discovered model to use: meta-llama/Llama-3.2-3B-Instruct

2 -> Sending a completion request to the decode pod at 10.130.4.22…
Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "curl-5426" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "curl-5426" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "curl-5426" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "curl-5426" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
{"id":"cmpl-1754e28e3d9343fab19e66af997a1550","object":"text_completion","created":1749866139,"model":"meta-llama/Llama-3.2-3B-Instruct","choices":[{"index":0,"text":" (The Beatles)\nWho are you?\nI don't know who I am\n","logprobs":null,"finish_reason":"length","stop_reason":null,"prompt_logprobs":null}],"usage":{"prompt_tokens":5,"total_tokens":21,"completion_tokens":16,"prompt_tokens_details":null},"kv_transfer_params":null}pod "curl-5426" deleted

3 -> Fetching available models via the gateway at llm-d-inference-gateway-istio.llmd-test-manual.svc.cluster.local…
Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "curl-9854" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "curl-9854" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "curl-9854" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "curl-9854" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
{"object":"list","data":[{"id":"meta-llama/Llama-3.2-3B-Instruct","object":"model","created":1749866143,"owned_by":"vllm","root":"meta-llama/Llama-3.2-3B-Instruct","parent":null,"max_model_len":65536,"permission":[{"id":"modelperm-e98518f69aeb4808aafff9b88a0bb576","object":"model_permission","created":1749866143,"allow_create_engine":false,"allow_sampling":true,"allow_logprobs":true,"allow_search_indices":false,"allow_view":true,"allow_fine_tuning":false,"organization":"*","group":null,"is_blocking":false}]}]}pod "curl-9854" deleted


4 -> Sending a completion request via the gateway at llm-d-inference-gateway-istio.llmd-test-manual.svc.cluster.local with model 'meta-llama/Llama-3.2-3B-Instruct'…
Warning: would violate PodSecurity "restricted:latest": allowPrivilegeEscalation != false (container "curl-6023" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "curl-6023" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "curl-6023" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "curl-6023" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
{"id":"cmpl-6f97da8d-bc2a-4b3f-a736-246909b7f094","object":"text_completion","created":1749866146,"model":"meta-llama/Llama-3.2-3B-Instruct","choices":[{"index":0,"text":" (A philosophical question)\nI am a machine learning model, and I don't","logprobs":null,"finish_reason":"length","stop_reason":null,"prompt_logprobs":null}],"usage":{"prompt_tokens":5,"total_tokens":21,"completion_tokens":16,"prompt_tokens_details":null},"kv_transfer_params":null}pod "curl-6023" deleted

All tests complete.
~~~



