import requests
import os
import dotenv
import re
from typing import List
import csv
import emoji
from sonar_evaluations import SonarEvaluations

dotenv.load_dotenv("./.env", override=True)

class SonarAndGitEvaluation:
    def __init__(
        self, org_or_user, output_file_name, git_token, sonar_token, has_project=False
    ) -> None:
        self.base_url = "https://api.github.com"
        self.organization_name = org_or_user
        self.git_token = git_token
        self.sonar_token = sonar_token
        self.output_file_name = output_file_name
        self.has_project = has_project
        self.create_csv()

    def make_many_evaluations(self):
        """
        Realiza a avaliação de diversos repositórios baseado nas funções da classe, adiciona cada critério
        em uma chave de objeto, e chama funções para criar e salvar novos registros no arquivo csv.
        """
        self.repositories: list = self.get_repositories()
        if self.has_project:
            self.projects: list = self.get_cards_of_projects()

        for repository in self.repositories:
            self.make_evaluation(repository)

    def make_evaluation(self, repository_name):
        evaluation = {"name": repository_name}
        evaluation["languages"] = self.get_languages_of_repository(repository_name)
        evaluation["quantity_of_pull_requests"] = self.get_quantity_of_pull_requests(
            repository_name
        )
        branches = self.get_branches(repository_name)
        evaluation["has_git_flow"] = self.check_git_flow(branches)
        commits = self.get_commits(repository_name)
        commits_info = self.get_commits_information(commits)
        evaluation["quantity_of_commits"] = commits_info["quantity"]
        commits_checked = self.check_commit_pattern(commits_info["commit_messages"])
        evaluation["commit_pattern_percent"] = commits_checked[
            "percentage_of_commits_with_pattern"
        ]
        evaluation["commits_per_type_percent"] = commits_checked[
            "commits_per_type_percentage"
        ]
        if self.has_project:
            evaluation["cards"] = self.check_project_in_repositories(repository_name)

        sonar = SonarEvaluations(
            self.sonar_token,
            repository_name,
            f"https://github.com/{self.organization_name}/{repository_name}",
        )
        sonar_analysis = sonar.make_evaluation()
        print(sonar_analysis)
        evaluation["total_of_issues"] = sonar_analysis["issues_total"]
        evaluation["issues_per_severity_quantity"] = sonar_analysis[
            "issues_per_severity_quantity"
        ]
        evaluation["issues_per_severity_percentage"] = sonar_analysis[
            "issues_per_severity_percentage"
        ]
        evaluation["code_smells"] = sonar_analysis["quantity_of_code_smells"]
        evaluation["quantity_of_bugs"] = sonar_analysis["quantity_of_bugs"]
        evaluation["quantity_of_vulnerabilities"] = sonar_analysis[
            "quantity_of_vulnerabilities"
        ]
        evaluation["percentage_of_code_duplication"] = sonar_analysis[
            "percentage_of_code_duplication"
        ]
        evaluation["security_hotspots"] = sonar_analysis[
            "quantity_of_security_hotspots"
        ]
        self.add_csv_record(self.file_name, evaluation)

    def create_csv(self):
        """
        Cria um arquivo csv com o nome recebido por paramêtro, e cria as colunas com os nomes corretos.

        Args:
            file_name (str): Nome do arquivo que deve ser criado.
            fields (list): Lista com os nomes das colunas do arquivo.
        """
        self.file_name = f"{self.output_file_name}.csv"

        fields = [
            "repositório",
            "linguagens",
            "quantidade_de_pull_requests",
            "git_flow",
            "quantidade_de_commits",
            "porcentagem_de_commits_no_padrão",
            "porcentagem_de_commits_por_tipo",
        ]

        if self.has_project:
            fields.append("cards_por_coluna")
        fields += [
            "total_de_issues",
            "quantidade_de_issues_por_severidade",
            "porcentagem_de_issues_por_severidade",
            "quantidade_de_code_smells",
            "quantidade_de_bugs",
            "quantidade_de_vulnerabilidades",
            "porcentagem_de_duplicação_de_código",
            "quantidade_de_pontos_de_acesso_de_segurança",
        ]

        with open(self.file_name, "w", newline="", encoding="utf-8-sig") as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=fields)
            csv_writer.writeheader()

    def add_csv_record(self, file_name, record):
        """
        Abre um arquivo baseado no nome passado e adiciona uma nova linha com as informações de avaliação de repositório.

        Args:
            file_name (str): Nome do arquivo que deve ser criado.
            record (obj): Objeto com os dados e avaliação de um repositório.
        """
        with open(file_name, "a", newline="", encoding="utf-8-sig") as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=record.keys())
            csv_writer.writerow(record)

    def make_request(self, url):
        """
        Realiza uma solicitação HTTP do tipo GET e retorna o resultado como JSON.
        Trata a paginação, caso tenha novas páginas, com mais registros, adiciona à lista de resultados.

        Args:
            url (str): A URL para a qual a solicitação GET será feita.

        Returns:
            list: Uma lista contendo os resultados da solicitação HTTP.
        """
        full_path = f"{self.base_url}/{url}?per_page=100&page="
        result = []
        page = 1
        rel_next = True
        while rel_next:
            print(rel_next)
            response = requests.get(
                full_path,
                headers={"Authorization": f"Bearer {self.git_token}"},
            )
            print(response.json())
            result += response.json()

            if response.headers.get(
                "Link"
            ) is not None and 'rel="next"' in response.headers.get("Link"):
                page += 1
            else:
                rel_next = False

        return result

    def get_repositories(self):
        """
        Realiza uma solicitação HTTP do tipo GET e retorna informações de repositórios
        da organização, que são tratados para retornar uma lista somente com os nomes.

        Args:
            url (str): A URL para a qual a solicitação GET será feita.

        Returns:
            list: Uma lista com o nome dos repositórios da organização.
        """
        org_repositories = self.make_request(f"orgs/{self.organization_name}/repos")
        repository_names = self.get_repository_name(org_repositories)
        return repository_names

    def get_repository_name(self, repositories):
        """
        Trata uma lista de objetos com informações sobre repositórios, para retornar apenas seus nomes.

        Args:
            repositories (list): Lista de objetos com informações de repositórios.

        Returns:
            list: Uma lista com o nome dos repositórios da organização.
        """
        repository_names = [repository["name"] for repository in repositories]
        return repository_names

    def get_repository_info(self, repository_name, extra_path=None):
        """
        Busca informações sobre certo repositório, pode receber um extra_path para retornar
        informações específicas sobre o mesmo.

        Args:
            repository_name (str): Nome do repositório sobre o qual as informações serão resgatadas.
            extra_path (str): Caminho de url adicional, para buscar informações específicas sobre repositório.

        Returns:
            (list|obj): Retorna uma lista com informações sobre um repositório.
        """
        path = f"repos/{self.organization_name}/{repository_name}{extra_path if extra_path else ''}"
        repository = self.make_request(path)
        return repository

    def get_languages_of_repository(self, repository_name):
        """
        Busca quais são as linguagens utilizadas por um repositório.

        Args:
            repository_name (str): Nome do repositório sobre o qual as informações serão resgatadas.

        Returns:
            list: Retorna uma lista com as linguagens utilizadas no projeto.
        """
        not_languages = ["HTML", "CSS", "Roff"]
        languages = self.get_repository_info(repository_name, "/languages")
        return [language for language in languages if language not in not_languages]

    def get_commits(self, repository_name):
        """
        Busca informações sobre os commits de repositório.

        Args:
            repository_name (str): Nome do repositório sobre o qual as informações serão resgatadas.

        Returns:
            list: Retorna uma lista de objetos que possuem informações sobre os commits.
        """
        commits = self.get_repository_info(repository_name, "/commits")
        return commits

    def get_commits_information(self, commits: list):
        """
        Retira as mensagens da lista de objetos com informações de commits, coloca em uma lista, e conta a quantidade de commits.

        Args:
            commits (list): Lista de objetos com informações sobre commits

        Returns:
            obj: Objeto com a chave "commit_messages", que é uma lista com todas as mensagens de commit, e a chave "quantity", que traz a quantidade de commits do repositório
        """
        quantity_of_commits = 0
        commit_messages = []

        for commit in commits:
            quantity_of_commits += 1
            commit_messages.append(commit["commit"]["message"])

        return {"commit_messages": commit_messages, "quantity": quantity_of_commits}

    def check_commit_pattern(self, list_of_commits):
        """
        Recebe a lista com mensagens dos commits, aplica uma expressão regular para avaliar se
        atende ao padrão de commit, e chama outras funções, para retornar a porcentagem de commits
        que estão padronizados, quantidade de commits por tipo, e porcentagem de commits por tipo.

        Args:
            list_of_commits (list): lista com mensagens de commit

        Returns:
            obj: objeto contendo uma chave de porcentagem de commits no padrão, commits por tipo
            e porcentagem de commits por tipo, todos com valores numéricos, com no máximo 2 casas após a virgula.
        """
        commits_per_type = {}
        commit_pattern = re.compile(
            r"^(docs|doc|fix|style|feat|refactor|perf|test|build|ci|chore|revert)(\(.*\))?:(\s){0,4}(\S){1}(.|\n)*$"
        )
        commits_with_pattern = 1
        commits_without_pattern = 0
        for commit_message in list_of_commits[:-1]:
            if commit_pattern.match(commit_message):
                commit_type = self.get_commit_type(commit_message)
                commits_per_type[commit_type] = commits_per_type.get(commit_type, 0) + 1
                commits_with_pattern += 1
            else:
                commits_without_pattern += 1

        total = commits_without_pattern + commits_with_pattern
        percentage_of_commits_with_pattern = round(
            (commits_with_pattern / total) * 100, 2
        )

        commits_per_type_percentage = self.get_commits_per_type_percentage(
            commits_per_type
        )

        return {
            "percentage_of_commits_with_pattern": percentage_of_commits_with_pattern,
            "commits_per_type": commits_per_type,
            "commits_per_type_percentage": commits_per_type_percentage,
        }

    def get_commit_type(self, commit_message):
        """
        Recebe a mensagem de commit e retira o tipo do commit baseado em expressão regular

        Args:
            commit_message (str): texto com a mensagem de commit

        Returns:
            str: texto com o tipo do commit
        """
        type_pattern = re.compile(f"^[a-zA-Z]+")
        commit_type = type_pattern.search(commit_message)
        return commit_type[0]

    def get_commits_per_type_percentage(self, commits_per_type):
        """
        Recebe um objeto de commits por tipo e converte esses valores de quantidade, para porcentagem.

        Args:
            commits_per_type (obj): objeto com chaves representando tipo de commit, e um valor numérico do tipo
            inteiro, que representa a quantidade.

        Returns:
            float: número que representa a porcentagem de commits por tipo
        """
        total_commits = sum(commits_per_type.values())

        commits_per_type_percentage = {}

        for type, count in commits_per_type.items():
            commits_per_type_percentage[type] = round((count / total_commits) * 100, 2)

        return commits_per_type_percentage

    def get_branches(self, repository_name):
        """
        Busca informações das branchs de um repositório e devolve uma lista com os nomes dessas branches.

        Args:
            repository_name (str): Nome do repositório sobre o qual as informações serão resgatadas.

        Returns:
            list: Lista com os nomes das branches existentes no projeto
        """
        branches = self.get_repository_info(repository_name, "/branches")
        branche_names = [branch['name'] for branch in branches]
        return branche_names

    def check_git_flow(self, branch_names: List[str]):
        """
        Recebe lista de branches de um repositório, e avalia se está utilizando o gitflow.
        Baseado nas branches necessárias para se enquadrar como uso de gitflow.

        Args:
            branch_names (list): lista com nomes de branches.

        Returns:
            bool: True ou False baseado no requisito de atender gitflow.
        """
        pattern = re.compile(r"(feature|develop|master|main)")
        key_words = {"feature", "develop"}
        principal_branchs = {"main", "master"}

        itens_found = set()

        for name in branch_names:
            name = name.lower()
            if pattern.search(name):
                p = pattern.search(name)
                itens_found.add(p[0])

        if itens_found.issuperset(key_words) and itens_found.intersection(
            principal_branchs
        ):
            return True
        else:
            return False

    def get_quantity_of_pull_requests(self, repository_name):
        """
        Busca a quantidade de pull requests de um repositório.

        Args:
            repository_name (str): Nome do repositório sobre o qual as informações serão resgatadas.

        Returns:
            int: Número de pull requests realizados no repositório.
        """
        pull_requests = self.get_repository_info(repository_name, "/pulls")
        return len(pull_requests)

    def get_cards_of_projects(self):
        """
        Busca informações dos cards de todos os projetos de uma organização, através de uma requisição HTTP do tipo POST,
        utilizando graphQL.

        Returns:
            list: Lista com informações de cards de cada projeto de uma organização do Gitub.
        """
        org = self.organization_name
        query = "{organization(login:" + f"'{org}'" + "){ projectsV2(first: 100) { nodes { title items(first: 100) { nodes { content { ... on DraftIssue { id } } status: fieldValueByName(name: 'Status') { ... on ProjectV2ItemFieldSingleSelectValue { column: name updatedAt } } } } } } } }"

        result = requests.post(
            f"{self.base_url}/graphql",
            headers={"Authorization": f"Bearer {self.git_token}"},
            json={"query": query},
        )

        return result.json()["data"]["organization"]["projectsV2"]["nodes"]

    def check_project_in_repositories(self, repository_name):
        """
        Baseado nos padrões de nome pré-definidos para projetos e repositórios, encontra os cards do repositório específico, contabiliza quantos cards estão em cada
        coluna.

        Args:
            repository_name (str): Nome do repositório sobre o qual as informações serão resgatadas.

        Returns:
            obj: objeto com o nome de cada coluna como chave, e um valor inteiro, representando a quantidade de cards na coluna.
        """
        card_columns = {
            "New": 0,
            "Backlog": 0,
            "Ready": 0,
            "progress": 0,
            "Blocked": 0,
            "review": 0,
            "Done": 0,
        }
        name_with_space = ""
        for letter in repository_name:
            if letter.isupper():
                name_with_space += " " + letter
            else:
                name_with_space += letter
        project_name = "Backlog -" + name_with_space
        for project in self.projects:
            if project_name == project["title"]:
                for card in project["items"]["nodes"]:
                    card_column = emoji.demojize(card["status"]["column"]).split(" ")[
                        -1
                    ]
                    if card_column in card_columns:
                        card_columns[card_column] += 1
                    else:
                        card_columns[card_column] = 1
        return card_columns

## Início da execução

analyzer = SonarAndGitEvaluation(
    "SergioRicJr", "analise_sonar_e_github", os.getenv("GIT_TOKEN"), os.getenv("SONAR_TOKEN")
)
analyzer.make_evaluation("todo-api")
