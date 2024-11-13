VERSION=v1
DOCKERUSER=pradzzyy

build:
	docker build -t demucs-rest .

push:
	docker tag demucs-rest $(DOCKERUSER)/demucs-rest:$(VERSION)
	docker push $(DOCKERUSER)/demucs-rest:$(VERSION)
	docker tag demucs-rest $(DOCKERUSER)/demucs-rest:latest
	docker push $(DOCKERUSER)/demucs-rest:latest

deploy:
	kubectl apply -f rest-server-deployment.yaml
	kubectl apply -f rest-server-service.yaml
	kubectl apply -f rest-ingress.yaml

clean:
	kubectl delete deployment rest-server
	kubectl delete service rest-server
	kubectl delete ingress rest-server-ingress

redo:
	make clean
	make build
	make push
	make deploy