
backend_storage:
	docker-compose -f etc/elasticsearch/docker-compose.yml up

collector:
	docker-compose -f etc/jaeger-collector/docker-compose.yml up

agent:
	docker-compose -f etc/jaeger-agent/docker-compose.yml up

query:
	docker-compose -f etc/jaeger-query/docker-compose.yml up

pypi:
	docker-compose -f etc/pypi/docker-compose.yml up
