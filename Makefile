IMAGE_TAG=execution-service:0.0.2

docker-build:
	docker build -t $(IMAGE_TAG) -f deployments/Dockerfile .

deploy_k8s:
	kubectl apply -f deployments/namespace.yaml
	kubectl apply -f deployments/configmap.yaml
	kubectl apply -f deployments/deployment.yaml
	kubectl apply -f deployments/service.yaml

deploy: docker-build deploy_k8s