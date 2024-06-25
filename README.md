
# Bot para automação de avaliação de repositórios

Este bot foi desenvolvido para automatizar o processo de avaliação de repositórios. Ele utiliza a API do Github. Mais informações do uso da API do Github podem ser acessadas através deste [repositório](https://github.com/SergioRicJr/github_api_documentation). Além disso, foi utilizado também o SonarQube para realizar análise aprofundada sobre diversos aspectos de qualidade do código.

## O que ele gera
Gera um arquivo csv com informações sobre repositórios do GitHub. Os dados trazidos são os seguintes:

- [x]  quantidade de commits
- [x]  quantidade de pull requests
- [x]  quantidade de cards em cada coluna
- [x]  linguagens utilizadas no projeto
- [x]  se o repositório adotou o Git Flow, ou não
- [x]  quantidade de commits
- [x]  porcentagem de commits padronizados de acordo com o conventional commits
- [x]  quantidade total de issues
- [x]  quantidade de issues por severidade
- [x]  porcentagem de issues por severidade
- [x]  porcentagem de duplicação de código
- [x]  quantidade de hotspots de segurança
- [x]  quantidade de issues do tipo bug
- [x]  quantidade de issues do tipo vulnerabilidade
- [x]  quantidade de issues do tipo code smell


## Requisitos

- Python 3.11
- Docker 
- Docker Compose

## Como baixar

- **Clonar o repositório**: Abra o terminal ou prompt de comando e navegue até o diretório onde deseja armazenar o código fonte do bot. Em seguida, execute o seguinte comando para clonar o repositório:

```
    git clone https://github.com/SergioRicJr/sonar_and_github_bot
```
- **Navegar até o repositório**: No terminal ou prompt de comando, navegue até o diretório recém-clonado:

```
    cd sonar_and_github_bot
```

- **Abrir o VSCode**: Após clonar o repositório, você pode abrir o Visual Studio Code (VSCode) para visualizar e editar o código fonte. Execute o seguinte comando:

```
    code .
```

Isso abrirá o VSCode no diretório do seu projeto, pronto para ser explorado e editado.

## Como rodar

- **Rodar SonarQube com Docker**: para rodar o SonarQube, abra o terminal e navegue para a pasta "sonar", e crie os containers do SonarQube:

```
    cd sonar 
```
```
    docker-compose up 
```

obs: certifique-se de que o docker desktop esteja ativo se estiver usando windows

- **Acessar SonarQube**: Para o primeiro acesso, entre em [http://localhost:9000](http://localhost:9000), e nos campos de username e senha, coloque "admin", após isso, basta criar uma nova senha, conforme o SonarQube irá requisitar.

- **Criar token do SonarQube e adicionar no .env**: Crie um arquivo chamado ".env", crie uma variável chamada "SONAR_TOKEN", e adicione o valor do token criado no Sonar. Para criar o token do sonar, acesse o SonarQube que está rodando com Docker, e siga o tutorial deste [Site](https://docs.sonarsource.com/sonarqube/latest/user-guide/user-account/generating-and-using-tokens).

- **Adicionar token do GitHub**: Ainda no arquivo ".env", crie uma variável chamada "GIT_TOKEN" e coloque o valor do token do GitHub. Na documentação deste [repositório](https://github.com/SergioRicJr/github_api_documentation) se encontra o tutorial para conseguir esse token.

- **Criar ambiente virtual**: Antes de baixar as dependências, digite o seguinte comando para criar um ambiente virtual:

```
    python -m venv ./venv
```

- **Ativar ambiente virtual**: Para ativar o ambiente, digite o seguinte comando:

```
    ./venv/Scripts/activate
```

- **Instalar das dependências**: Certifique-se de ter o Python 3.11 instalado em seu sistema. Em seguida, você pode instalar as dependências do projeto executando o seguinte comando:

```
    pip install -r requirements.txt
```

- **Configurar quais funções usar**: No final do arquivo main.py, você pode configurar o nome do repositório ou organização, o nome do arquivo gerado, e se for uma organização, se ela possui projetos ou não. No exemplo abaixo está sendo passado o nome de um perfil do github, e o nome do repositório é especificado ao chamar a função "make_evaluation". Obs: Se utilizar sem configurar, terá o resultado da avaliação do repositório deste [link](https://github.com/SergioRicJr/todo-api)

```
    analyzer = SonarAndGitEvaluation(
        "SergioRicJr", "analise_sonar_e_github", os.getenv("GIT_TOKEN"), os.getenv("SONAR_TOKEN")
    )
    analyzer.make_evaluation("todo-api")
```

- **Rodar o projeto**: Após os passos anteriores, basta digitar o seguinte comando no terminal para gerar o csv com as avaliações:

```
    python main.py
```

## Configurações adicionais

- **Parâmetro "has_project" no construtor da classe SonarAndGitEvaluation**: Este parâmetro é utilizado para adicionar a análise de cards e suas posições em projetos do repositório, seguindo o padrões pré-definidos de nome dos repositórios e projetos de uma organização. Deve ser passado como True somente nesse caso, por padrão ele é False, pois em outros repositórios pode ser que não haja um backlog, não sendo possível fazer essa análise.

- **Análise de repositórios de uma organização**: Para realizar a análise de todos os repositórios de uma organização, o método utilizado é o make_many_evaluations(). Não é necessário passar parâmetros pois todas as informações necessárias já são passadas no método construtor da classe SonarAndGitEvaluation.

- **Análise de um único repositório**: Para analisar somente um repositório, os parâmetros passados no construtor da classe ScientificEvaluation são os mesmos para análise de repositórios de uma organização do GitHub, porém, ao invés do nome de organização, pode ser passado o nome do usuário dono do repositório ou uma organização. O método a ser chamado é o make_evaluation(), passando como paramêtro o nome do repositório.