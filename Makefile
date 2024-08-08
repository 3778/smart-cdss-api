envvar_token=SMARTCDSS_SECRET_TOKEN
envvar_ui_token=UI_SMARTCDSS_SECRET_TOKEN

install:
	@pip3 install poetry
	@poetry install
	@P=$$(poetry env info -p)/bin/activate;\
	if $$(grep -q $(envvar_token) $$P);\
	then \
	:; \
	else \
	read -p "Enter API Security Token:" token;\
	read -p "Enter UI Security Token:" ui_token;\
	echo "export $(envvar_token)=$$token" >> $$P;\
	echo "export $(envvar_ui_token)=$$ui_token" >> $$P; \
	fi
	@poetry run aws configure

launch-jupyter:
	@. $$(poetry env info -p)/bin/activate;\
	jupyter notebook

launch-api:
	@. $$(poetry env info -p)/bin/activate;\
	python3 application.py

launch-ui:
	@. $$(poetry env info -p)/bin/activate;\
	streamlit run smart_cdss_api/ui/ui_application.py

launch-analytics:
	@. $$(poetry env info -p)/bin/activate;\
	streamlit run smart_cdss_api/ui/ui_analytics.py

launch-documentation:
	@. $$(poetry env info -p)/bin/activate;\
	head -1 README.md > .Documentation.md;\
	echo "## Documentação" >> .Documentation.md;\
	awk 'found,0;/## Documentação/{found=1}' README.md >> .Documentation.md;\
	grip .Documentation.md 0.0.0.0:8505;\
	rm .Documentation.md

check-pep:
	@. $$(poetry env info -p)/bin/activate;\
	pycodestyle wsgi.py;\
	pycodestyle application.py --ignore=E722;\
	pycodestyle ui_application.py --ignore=E741;\
	pycodestyle ui_analytics.py --ignore=E741;\
	pycodestyle api/data/load.py;\
	pycodestyle api/conf/conf.py

setup-zappa:
	# Create Poetry for Zappa
	@mkdir -p .zappa
	@cp pyproject.toml .zappa/pyproject.toml
	@sed -i 's/smart_cdss_api/zappa_smart_cdss_api/g' .zappa/pyproject.toml
	# Run Poetry and put Envvars
	@cd .zappa/; poetry install --no-dev
	@cd .zappa/;\
	PZ=$$(poetry env info -p)/bin/activate;\
	if $$(grep -q $(envvar_token) $$PZ);\
	then \
	:; \
	else \
	cd ..;\
	$-P=$$(poetry env info -p)/bin/activate;\
	([ $$? -ne 0 ] && read -p "Enter API Security Token:" token &&\
	echo "export $(envvar_token)=$$token" >> $$PZ) \
	|| (token=$$(grep '$(envvar_token)' $$P |\
	head -1) && \
	echo $$token >> $$PZ); \
	fi
	# Copy files to folder
	@cp -r smart_cdss_api/ wsgi.py application.py .zappa/
	@cd .zappa/;\
	rm -rf smart_cdss_api/ui;\
	. $$(poetry env info -p)/bin/activate;\
	envsubst < ../zappa_settings.json.tpl > zappa_settings.json

zappa-deploy:
	@make setup-zappa
	@cd .zappa;\
	. $$(poetry env info -p)/bin/activate;\
	zappa deploy
	@rm -rf .zappa

zappa-update:
	@make setup-zappa
	@cd .zappa;\
	. $$(poetry env info -p)/bin/activate;\
	zappa update
	@rm -rf .zappa

zappa-undeploy:
	@make setup-zappa
	@cd .zappa;\
	. $$(poetry env info -p)/bin/activate;\
	zappa undeploy
	@rm -rf .zappa

deploy:
	@. $$(poetry env info -p)/bin/activate;\
	gunicorn --bind 0.0.0.0:5010 wsgi:app
