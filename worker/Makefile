VERSION=v1
DOCKERUSER=pradzzyy

build:
	docker build -f Dockerfile -t demucs-worker .
push:
	docker tag demucs-worker $(DOCKERUSER)/demucs-worker:$(VERSION)
	docker push $(DOCKERUSER)/demucs-worker:$(VERSION)
	docker tag demucs-worker $(DOCKERUSER)/demucs-worker:latest
	docker push $(DOCKERUSER)/demucs-worker:latest

deploy:
	kubectl apply -f worker-deployment.yaml

clean:
	kubectl delete deployment demucs-worker

redo:
	make clean
	make build
	make push
	make deploy