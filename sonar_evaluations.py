import os
from typing import Dict
import dotenv
import requests
import json
import time

dotenv.load_dotenv("./.env", override=True)


class SonarEvaluations:
    def __init__(self, sonar_token, project_name, github_url) -> None:
        self.sonar_token = sonar_token
        self.project_key = project_name
        self.project_name = project_name
        self.github_url = github_url

    def make_evaluation(self):
        """
        Realiza uma avaliação do projeto no SonarQube e retorna diversas métricas de qualidade de código.

        Returns:
            dict: Um dicionário contendo métricas como número total de issues, quantidade de issues por severidade,
                  porcentagem de duplicação de código, quantidade de hotspots de segurança, entre outras.
        """
        self.create_sonar_project()
        self.create_sonar_project_properties()
        self.dowload_github_files(self.github_url)
        self.make_sonarqube_analysis()

        analysis_ready = False

        while not analysis_ready:
            analysis = self.make_request(
                "project_analyses/search", f"project={self.project_key}"
            )["analyses"]
            if analysis != []:
                analysis_ready = True
            time.sleep(1)

        code_duplication = self.get_code_duplication()
        maintainability_issues = self.get_quantity_of_maintainability_issues()
        reliability_issues = self.get_quantity_of_reliability_issues()
        security_issues = self.get_quantity_of_security_issues()

        issues_per_severity = self.check_issues_per_severity_quantity(
            maintainability_issues, reliability_issues, security_issues
        )
        total_of_issues = issues_per_severity["total"]
        issues_per_severity_percentage = self.get_percentage_of_values(
            issues_per_severity
        )
        quantity_of_security_hotspots = self.get_quantity_of_security_hotspots()
        quantity_of_bugs = self.get_bug_issues()
        quantity_of_vulnerabilities = self.get_vulnerabiity_issues()
        quantity_of_code_smells = self.get_code_smells_issues()

        return {
            "issues_total": total_of_issues,
            "issues_per_severity_quantity": issues_per_severity,
            "issues_per_severity_percentage": issues_per_severity_percentage,
            "percentage_of_code_duplication": code_duplication,
            "quantity_of_security_hotspots": quantity_of_security_hotspots,
            "quantity_of_bugs": quantity_of_bugs,
            "quantity_of_vulnerabilities": quantity_of_vulnerabilities,
            "quantity_of_code_smells": quantity_of_code_smells,
        }

    def make_request(self, extra_path, query):
        """
        Realiza uma requisição à API do SonarQube, já com a autenticação necessária e organizando parâmetros e queries.

        Args:
            extra_path (str): Caminho adicional para a requisição.
            query (str): Parâmetros de consulta para a requisição.

        Returns:
            dict: Resposta da requisição em formato JSON.
        """
        response = requests.get(
            f"http://localhost:9000/api/{extra_path}?{query}",
            headers={"Authorization": f"Bearer {self.sonar_token}"},
        )
        json_of_response = response.json()
        return json_of_response

    def create_sonar_project(self):
        """
        Cria um projeto no SonarQube.

        Returns:
            None
        """
        requests.post(
            f"http://localhost:9000/api/projects/create?project={self.project_name}&name={self.project_key}",
            headers={"Authorization": f"Bearer {self.sonar_token}"},
        )

    def dowload_github_files(self, github_url, repository_path="github_repository"):
        """
        Baixa os arquivos do repositório GitHub e coloca na pasta correta para análise do SonarQube,
        além de fazer o tratamento e apagar os arquivos para baixar os próximos.

        Args:
            github_url (str): URL do repositório GitHub.
            repository_path (str): Caminho onde os arquivos do repositório serão salvos.

        Returns:
            None
        """
        if os.path.exists(repository_path):
            os.system(f"rmdir /s /q {repository_path}")
        os.mkdir("github_repository")
        os.system(f"cd {repository_path} && git clone {github_url}")

    def make_sonarqube_analysis(self):
        """
        Realiza uma análise do projeto no SonarQube, baseado no docker-compose configurado.

        Returns:
            None
        """
        os.system("docker-compose up --build")

    def create_sonar_project_properties(
        self,
        sonar_sources="./github_repository",
        sonar_host_url="http://sonarqube:9000",
    ):
        """
        Cria o arquivo de propriedades do projeto SonarQube.

        Args:
            sonar_sources (str): Caminho para os arquivos fonte do projeto.
            sonar_host_url (str): URL do host do SonarQube.

        Returns:
            None
        """
        with open("sonar-project.properties", "w") as file:
            file.write("sonar.scm.exclusions.disabled=true\n")
            file.write(f"sonar.sources={sonar_sources}\n")
            file.write(f"sonar.token={self.sonar_token}\n")
            file.write(f"sonar.host.url={sonar_host_url}\n")
            file.write(f"sonar.projectKey={self.project_key}\n")

    def get_value_of_component_response(self, response):
        """
        Obtém o valor de uma resposta de componente.

        Args:
            response (dict): Resposta da requisição em formato JSON.

        Returns:
            dict: dicionário com dados retornados pelo json.
        """
        response = response["component"]["measures"]
        return response[0]["value"] if len(response) > 0 else 0

    def get_code_duplication(self):
        """
        Obtém a porcentagem de duplicação de código.

        Returns:
            float: Porcentagem de duplicação de código.
        """
        code_duplication = self.make_request(
            extra_path="measures/component",
            query=f"component={self.project_key}&metricKeys=duplicated_lines_density",
        )
        return self.get_value_of_component_response(code_duplication)

    def get_quantity_of_reliability_issues(self):
        """
        Obtém a quantidade de issues de confiabilidade.

        Returns:
            dict: Quantidade de issues de confiabilidade, separado em chaves que dizem o nível severidade e valor com quantidade.
        """
        reliability_issues = self.make_request(
            extra_path="measures/component",
            query=f"component={self.project_key}&metricKeys=reliability_issues",
        )
        return self.get_value_of_component_response(reliability_issues)

    def get_quantity_of_security_issues(self):
        """
        Obtém a quantidade de issues de segurança.

        Returns:
            int: Quantidade de issues de segurança, separado em chaves que dizem o nível severidade e valor com quantidade..
        """
        security_issues = self.make_request(
            extra_path="measures/component",
            query=f"component={self.project_key}&metricKeys=security_issues",
        )
        return self.get_value_of_component_response(security_issues)

    def get_quantity_of_maintainability_issues(self):
        """
        Obtém a quantidade de issues de manutenibilidade.

        Returns:
            int: Quantidade de issues de manutenibilidade, separado em chaves que dizem o nível severidade e valor com quantidade..
        """
        maintainability_issues = self.make_request(
            extra_path="measures/component",
            query=f"component={self.project_key}&metricKeys=maintainability_issues",
        )
        return self.get_value_of_component_response(maintainability_issues)

    def get_quantity_of_security_hotspots(self):
        """
        Obtém a quantidade de hotspots de segurança.

        Returns:
            int: Quantidade de hotspots de segurança.
        """
        security_hotspots = self.make_request(
            extra_path="measures/component",
            query=f"component={self.project_key}&metricKeys=security_hotspots",
        )
        return self.get_value_of_component_response(security_hotspots)

    def get_bug_issues(self):
        """
        Obtém a quantidade de issues de bugs.

        Returns:
            int: Quantidade de issues de bugs.
        """
        bugs = self.make_request(
            extra_path="measures/component",
            query=f"component={self.project_key}&metricKeys=bugs",
        )
        return self.get_value_of_component_response(bugs)

    def get_code_smells_issues(self):
        """
        Obtém a quantidade de issues de smells de código.

        Returns:
            int: Quantidade de issues de smells de código.
        """
        code_smells = self.make_request(
            extra_path="measures/component",
            query=f"component={self.project_key}&metricKeys=code_smells",
        )
        return self.get_value_of_component_response(code_smells)

    def get_vulnerabiity_issues(self):
        """
        Obtém a quantidade de issues de vulnerabilidades.

        Returns:
            int: Quantidade de issues de vulnerabilidades.
        """
        vulnerability_issues = self.make_request(
            extra_path="measures/component",
            query=f"component={self.project_key}&metricKeys=vulnerabilities",
        )
        return self.get_value_of_component_response(vulnerability_issues)

    def check_issues_per_severity_quantity(
        self, maintainability_issues, reliability_issues, security_issues
    ):
        """
        Verifica a quantidade de issues por severidade de todos os tipos de issue.

        Args:
            maintainability_issues (int): Quantidade de issues de manutenibilidade.
            reliability_issues (int): Quantidade de issues de confiabilidade.
            security_issues (int): Quantidade de issues de segurança.

        Returns:
            dict: Um dicionário contendo a quantidade de issues por severidade.
        """
        maintainability_issues = json.loads(maintainability_issues)
        reliability_issues = json.loads(reliability_issues)
        security_issues = json.loads(security_issues)

        total_low = (
            maintainability_issues["LOW"]
            + reliability_issues["LOW"]
            + security_issues["LOW"]
        )
        total_medium = (
            maintainability_issues["MEDIUM"]
            + reliability_issues["MEDIUM"]
            + security_issues["MEDIUM"]
        )
        total_high = (
            maintainability_issues["HIGH"]
            + reliability_issues["HIGH"]
            + security_issues["HIGH"]
        )
        total_issues = (
            maintainability_issues["total"]
            + reliability_issues["total"]
            + security_issues["total"]
        )

        return {
            "total_low": total_low,
            "total_medium": total_medium,
            "total_high": total_high,
            "total": total_issues,
        }

    def get_percentage_of_values(self, object: Dict[str, int]):
        """
        Calcula a porcentagem dos valores em relação ao total, com chaves genéricas.

        Args:
            object (Dict[str, int]): Um dicionário contendo os valores a serem calculados, e uma chave total para o valor total dos itens.

        Returns:
            dict: Um dicionário contendo as porcentagens calculadas.
        """
        total = object.get("total", 0)

        percentage = {}

        if total == 0:
            return percentage

        for key, value in object.items():
            if key != "total":
                percentage[key] = round((value / total) * 100, 2)
        return percentage
