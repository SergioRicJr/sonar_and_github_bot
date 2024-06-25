FROM sonarsource/sonar-scanner-cli:10

COPY sonar-project.properties /opt/sonar-scanner/conf/
COPY . .

ENTRYPOINT ["sonar-scanner"]