migrate:
	docker-compose exec amura_service_mac /bin/bash -c "python app/manage.py db init"
	docker-compose exec amura_service_mac /bin/bash -c "python app/manage.py db migrate"
	docker-compose exec amura_service_mac /bin/bash -c "python app/manage.py db upgrade"