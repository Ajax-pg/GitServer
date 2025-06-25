from datetime import datetime
import ast
from github import Github
from pathlib import PurePosixPath




class GitHubRepo:
    def __init__(self, token: str, repo_name: str):
        self.token = token
        self.repo_name = repo_name
        self.client = Github(self.token)

        try:
            self.repo = self.client.get_user().get_repo(self.repo_name)
            print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] Successfully connected to repository '{self.repo_name}'.")
        except Exception as e:
            print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] Failed to connect to repository '{self.repo_name}': {e}")
            self.repo = None

    def get_repo(self):
        return self.repo



class GitHubRepoDev:
    def __init__(self, token: str, repo_name: str = None):
        self.token = token
        self.client = Github(self.token)
        self.repo_name = repo_name
        self.user = self.client.get_user()

        self.repo = None
        if repo_name:
            try:
                self.repo = self.user.get_repo(repo_name)
                print(f"[{datetime.now().strftime('%d/%m/%Y | %H:%M')}] Connected to repo: {repo_name}")
            except Exception as e:
                print(f"Error accessing repo: {e}")

    # === Repository ===
    def create_repo(self, name, private=True, description=""):
        repo = self.user.create_repo(name=name, private=private, description=description)
        print(f"Repository '{name}' created.")
        return repo

    def delete_repo(self):
        if self.repo:
            self.repo.delete()
            print(f"Repository '{self.repo_name}' deleted.")

    def rename_repo(self, new_name):
        if self.repo:
            self.repo.edit(name=new_name)
            print(f"Repository renamed to '{new_name}'")

    def get_repo_info(self):
        if self.repo:
            return {
                "name": self.repo.name,
                "full_name": self.repo.full_name,
                "description": self.repo.description,
                "private": self.repo.private,
                "url": self.repo.html_url,
                "created_at": str(self.repo.created_at)
            }


    # === Hooks ===
    def list_hooks(self):
        return self.repo.get_hooks()

    def create_hook(self, config, events=["push"], active=True):
        """
        Creates a repository webhook.
        
        Args:
            config (dict): Configuration of the hook, e.g., {"url": "...", "content_type": "json"}
            events (list): Events that trigger the webhook (default is ["push"])
            active (bool): Whether the webhook is active (default is True)
        """
        try:
            self.repo.create_hook(
                name="web",  # fixed value, GitHub expects "web"
                config=config,
                events=events,
                active=active
            )
            print("✅ Webhook created successfully.")
        except Exception as e:
            print(f"❌ Failed to create webhook: {e}")

    def delete_hook(self, hook_id):
        hook = self.repo.get_hook(hook_id)
        hook.delete()
        print(f"Hook '{hook_id}' deleted.")




class File:
    def __init__(self, repo, file_path: str = "", new_content: str = "", source: str = "", destination: str = "", branch: str = "main"):
        self.repo = repo                   
        self.file_path = file_path
        self.new_content = new_content
        self.source = source
        self.destination = destination
        self.branch = branch
        
    def __cof__(self, repo, file_path: str = "", new_content: str = "", source: str = "", destination: str = "", branch: str = "main"):
        self.repo = repo                   
        self.file_path = file_path
        self.new_content = new_content
        self.source = source
        self.destination = destination
        self.branch = branch

    def read(self) -> str:
        file = self.repo.get_contents(self.file_path, ref=self.branch)
        print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] File '{self.file_path}' fetched successfully.")
        return file.decoded_content.decode()

    def update(self):
        file = self.repo.get_contents(self.file_path, ref=self.branch)
        self.repo.update_file(
            path=self.file_path,
            message="File updated via PyGithub",
            content=self.new_content,
            sha=file.sha,
            branch=self.branch
        )
        print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] File '{self.file_path}' updated successfully.")

    def create(self):
        self.repo.create_file(
            path=self.file_path,
            message="New file created via PyGithub",
            content=self.new_content,
            branch=self.branch
        )
        print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] File '{self.file_path}' created.")

    def delete(self):
        file = self.repo.get_contents(self.file_path, ref=self.branch)
        self.repo.delete_file(
            path=self.file_path,
            message="File deleted via PyGithub",
            sha=file.sha,
            branch=self.branch
        )
        print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] File '{self.file_path}' deleted.")

    def move(self):
        source = str(PurePosixPath(self.source))
        destination = str(PurePosixPath(self.destination))

        try:
            # Try file first
            content = self.repo.get_contents(source, ref=self.branch)
            self.repo.create_file(
                path=destination,
                message=f"Moved '{source}' to '{destination}'",
                content=content.decoded_content,
                branch=self.branch
            )
            self.repo.delete_file(
                path=source,
                message=f"Deleted '{source}' after moving",
                sha=content.sha,
                branch=self.branch
            )
            print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] File '{source}' moved to '{destination}'.")
        
        except Exception:
            # Try as folder
            try:
                items = self.repo.get_contents(source, ref=self.branch)
                if not items:
                    raise ValueError(f"Folder '{source}' is empty or does not exist.")

                for item in items:
                    sub_source = item.path
                    sub_rel = PurePosixPath(sub_source).relative_to(source)
                    sub_dest = str(PurePosixPath(destination) / sub_rel)

                    if item.type == "dir":
                        nested = File(self.repo, branch=self.branch, source=sub_source, destination=sub_dest)
                        nested.move()
                    else:
                        self.repo.create_file(
                            path=sub_dest,
                            message=f"Moved '{sub_source}' to '{sub_dest}'",
                            content=item.decoded_content,
                            branch=self.branch
                        )
                        self.repo.delete_file(
                            path=sub_source,
                            message=f"Deleted '{sub_source}' after moving",
                            sha=item.sha,
                            branch=self.branch
                        )

                # Attempt to remove empty source folder marker
                marker_path = f"{source}/.gitkeep"
                try:
                    self.repo.create_file(marker_path, "Remove folder marker", "", branch=self.branch)
                    sha = self.repo.get_contents(marker_path, ref=self.branch).sha
                    self.repo.delete_file(marker_path, "Deleted folder marker", sha=sha, branch=self.branch)
                except Exception:
                    pass

                print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] Folder '{source}' moved to '{destination}'.")

            except Exception as e:
                print(f"{datetime.now().strftime('[%d/%m/%Y | %H:%M]')} [GitHub] Error moving '{source}': {e}")




class Folder:
    def __init__(self, repo, path: str, branch: str = "main", new_path: str = ""):
        self.repo = repo
        self.path = str(PurePosixPath(path))
        self.new_path = str(PurePosixPath(new_path)) if new_path else ""
        self.branch = branch
        
    def __cof__(self, repo, path: str, branch: str = "main", new_path: str = ""):
        self.repo = repo
        self.path = str(PurePosixPath(path))
        self.new_path = str(PurePosixPath(new_path)) if new_path else ""
        self.branch = branch

    def _timestamp(self):
        return datetime.now().strftime("[%d/%m/%Y | %H:%M]")

    def create(self):
        try:
            marker_path = f"{self.path}/.gitkeep"
            self.repo.create_file(
                path=marker_path,
                message=f"Creating folder '{self.path}'",
                content="",
                branch=self.branch
            )
            print(f"{self._timestamp()} [GitHub] Folder '{self.path}' created with .gitkeep.")
        except Exception as e:
            print(f"{self._timestamp()} [GitHub] Error creating folder '{self.path}': {e}")

    def delete(self):
        try:
            items = self.repo.get_contents(self.path, ref=self.branch)
            for item in items:
                if item.type == "dir":
                    sub_folder = Folder(self.repo, path=item.path, branch=self.branch)
                    sub_folder.delete()
                else:
                    self.repo.delete_file(
                        path=item.path,
                        message=f"Deleting '{item.path}'",
                        sha=item.sha,
                        branch=self.branch
                    )
                    print(f"{self._timestamp()} [GitHub] Deleted file '{item.path}'.")

            # Attempt to delete the .gitkeep or residual marker
            marker_path = f"{self.path}/.gitkeep"
            try:
                marker = self.repo.get_contents(marker_path, ref=self.branch)
                self.repo.delete_file(
                    path=marker_path,
                    message="Deleting .gitkeep after folder cleanup",
                    sha=marker.sha,
                    branch=self.branch
                )
                print(f"{self._timestamp()} [GitHub] Deleted folder marker '{marker_path}'.")
            except:
                pass

            print(f"{self._timestamp()} [GitHub] Folder '{self.path}' deleted.")
        except Exception as e:
            print(f"{self._timestamp()} [GitHub] Error deleting folder '{self.path}': {e}")

    def move(self):
        if not self.new_path:
            raise ValueError("New path not provided for move operation.")

        try:
            items = self.repo.get_contents(self.path, ref=self.branch)
            for item in items:
                rel_path = PurePosixPath(item.path).relative_to(self.path)
                dest_path = str(PurePosixPath(self.new_path) / rel_path)

                if item.type == "dir":
                    subfolder = Folder(self.repo, path=item.path, new_path=dest_path, branch=self.branch)
                    subfolder.move()
                else:
                    self.repo.create_file(
                        path=dest_path,
                        message=f"Moving '{item.path}' to '{dest_path}'",
                        content=item.decoded_content,
                        branch=self.branch
                    )
                    self.repo.delete_file(
                        path=item.path,
                        message=f"Deleting original '{item.path}' after move",
                        sha=item.sha,
                        branch=self.branch
                    )
                    print(f"{self._timestamp()} [GitHub] Moved file '{item.path}' → '{dest_path}'.")

            # Clean up original folder marker
            marker_path = f"{self.path}/.gitkeep"
            try:
                self.repo.create_file(marker_path, "Remove folder marker", "", branch=self.branch)
                sha = self.repo.get_contents(marker_path, ref=self.branch).sha
                self.repo.delete_file(marker_path, "Deleted folder marker", sha=sha, branch=self.branch)
            except:
                pass

            print(f"{self._timestamp()} [GitHub] Folder '{self.path}' moved to '{self.new_path}'.")
        except Exception as e:
            print(f"{self._timestamp()} [GitHub] Error moving folder '{self.path}': {e}")

    def rename(self, new_name: str):
        new_path = str(PurePosixPath(self.path).parent / new_name)
        self.new_path = new_path
        self.move()


class server:
    def __init__(self, token, repo):
        """
        # Server (__init__)
        Parameters: token and repository (str, str)

        The purpose of this function is to pass parameters to the 'Server' class. This class was developed
        to manipulate data on a server, using GitHub as a repository. To use it, access your GitHub account,
        get the name of the desired repository and the corresponding access token.
        """
        try:
            self.token = token
            self.repo = repo
            self.G = GitHubRepoDev(token=self.token, repo_name=self.repo)
            self.repo = GitHubRepo(token=self.token, repo_name=self.repo).get_repo()
            time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            serv = f'''
= Note ================================================
Server initialized with:
[TIME]             [{time}]
[SERVER]                            [\033[34mON\033[0m]
[GUITHUB]                    [\033[33mCONNECTED\033[0m]
[REPOSITORY]                 [\033[33mCONNECTED\033[0m]
[TOKEN]                      [\033[33mCONNECTED\033[0m]
=======================================================
            '''
            print(serv)
        except Exception as e:
            print(f"Error initializing Server: {e}")
            raise
        
    def create_class(self, name):
        """
        # Server (CreateClass)
        Parameters: name (str)

        The purpose of this function is to create a class in the repository.
        """
        # Verifica se a pasta já existe
        try:
            self.repo.get_contents(f'{name}/', ref='main')
            print(f"Class '{name}' already exists in the repository '{self.repo}'.")
            return name
        except Exception:
            Folder(self.repo, f'{name}/', 'main').create()
            print(f"Class '{name}' created successfully in the repository '{self.repo}'.")
            return name

    def create_table(self, name, clas):
        """
        # Server (CreateTable)
        Parameters: name and clas (str, str)

        The purpose of this function is to create a table in the specified class.
        """
        # Verifica se o arquivo já existe
        try:
            self.repo.get_contents(f'{clas}/{name}.json', ref='main')
            print(f"Table '{name}' already exists in class '{clas}' of the repository '{self.repo}'.")
            return name
        except Exception:
            File(self.repo, f'{clas}/{name}.json', '{}',branch='main').create()
            print(f"Table '{name}' created successfully in class '{clas}' of the repository '{self.repo}'.")
            return name

    def insert_data(self, table, clas, name,  data):
        """
        # Server (insert_data_table)
        Parameters: table, clas, name and data (str, str, str, dict)

        The purpose of this function is to insert data into a specified table.
        """
        r = File(self.repo, f'{clas}/{table}.json', '{}',branch='main').read()
        DATA = ast.literal_eval(r)
        if name in DATA:
            print(f"Data with name '{name}' already exists in table '{table}'.")
            return
        DATA[name] = data
        File(self.repo, f'{clas}/{table}.json', f'{str(DATA)}',branch='main').update()
        print(f"Data inserted successfully into table '{table}' in class '{clas}' of the repository '{self.repo}'.")
        
    def remove_data(self, table, clas, name):
        """
        # Server (remove_data_table)
        Parameters: table, clas and name (str, str, str)

        The purpose of this function is to remove data from a specified table.
        """
        r = File(self.repo, f'{clas}/{table}.json', '{}',branch='main').read()
        DATA = ast.literal_eval(r)
        if name not in DATA:
            print(f"Data with name '{name}' does not exist in table '{table}'.")
            return
        del DATA[name]
        File(self.repo, f'{clas}/{table}.json', f'{str(DATA)}',branch='main').update()
        print(f"Data with name '{name}' removed successfully from table '{table}' in class '{clas}' of the repository '{self.repo}'.")
        
        
    def update_data(self, table, clas, name, data):
        """
        # Server (update_data)
        Parameters: table, clas, name, data (str, str, str, dict)

        The purpose of this function is to update data for a specific entry in a given table.
        """
        r = File(self.repo, f'{clas}/{table}.json', '{}',branch='main').read()
        DATA = ast.literal_eval(r)
        if name not in DATA:
            print(f"Data with name '{name}' does not exist in table '{table}'.")
            return
        DATA[name] = data
        File(self.repo, f'{clas}/{table}.json', f'{str(DATA)}',branch='main').update()
        print(f"Data with name '{name}' updated successfully in table '{table}' in class '{clas}' of the repository '{self.repo}'.")
            
    def get_data(self, table, clas):
        """
        # Server (get_data)
        Parameters: table, clas (str, str)

        The purpose of this function is to retrieve all data from a specified table in a given class.
        """
        r = File(self.repo, f'{clas}/{table}.json', '{}',branch='main').read()
        DATA = ast.literal_eval(r)
        print(f"Data from table '{table}' in class '{clas}' of the repository '{self.repo}':")
        print(DATA)
        return DATA
    
    def search_data(self, table, clas, name):
        """
        # Server (search_data)
        Parameters: table, clas, name (str, str, str)

        The purpose of this function is to search for a specific entry by name in a given table and class.
        """
        r = File(self.repo, f'{clas}/{table}.json', '{}',branch='main').read()
        DATA = ast.literal_eval(r)
        if name not in DATA:
            print(f"Data with name '{name}' does not exist in table '{table}'.")
            return
        print(f"Data with name '{name}' found in table '{table}' in class '{clas}' of the repository '{self.repo}':")
        print(DATA[name])
        return DATA[name]


    def remove_table(self, clas, table):
        """
        # Server (remove_table)
        Parameters: clas and table (str, str)

        The purpose of this function is to remove a specified table (JSON file) from a given class (folder) in the repository.
        """
        File(self.repo, f'{clas}/{table}.json', '{}',branch='main').delete()
        print(f"Table '{table}' removed successfully from class '{clas}' in the repository '{self.repo}'.")
                
    def remove_class(self, clas):
        """
        # Server (remove_class)
        Parameters: clas (str)

        The purpose of this function is to remove a specified class (folder) and all its contents from the repository.
        """
        Folder(self.repo, f'{clas}/', 'main').delete()
        print(f"Class '{clas}' removed successfully from the repository '{self.repo}'.")


        
            
# S = server('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', 'API')
# S.create_class('TESTE')
# S.create_table('TESTE', 'TESTE')
# S.insert_data('TESTE', 'TESTE', 'teste1', 'teste')
# S.insert_data('TESTE', 'TESTE', 'teste2', 'teste')
# S.get_data('TESTE', 'TESTE')
# S.search_data('TESTE', 'TESTE', 'teste1')
# S.update_data('TESTE', 'TESTE', 'teste1', 'TESTE')
# S.search_data('TESTE', 'TESTE', 'teste1')
# S.remove_data('TESTE', 'TESTE', 'teste1')
# S.get_data('TESTE', 'TESTE')
# S.remove_data('TESTE', 'TESTE', 'teste1')
# S.get_data('TESTE', 'TESTE')
# S.remove_table('TESTE', 'TESTE')
# S.remove_class('TESTE')