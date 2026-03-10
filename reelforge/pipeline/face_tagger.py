from jebin_lib import utils
from .. import config

def setup():
    cwd = "/tmp/FaceTagger"
    utils.setup_git_repo_get_install_pip(
        repo_url="https://github.com/jebin2/FaceTagger.git",
        target_path=cwd,
        pip_name="FaceTagger",
        requirements_file="requirements_auto_crop.txt"
    )
    if not utils.dir_exists(cwd):
        raise ValueError("FaceTagger not setup correctly.")

    python_path = os.path.expanduser("~/.pyenv/versions/FaceTagger_env/bin/python")
    cmd = f"{python_path} insight_face_manager.py '{cache_path}' real"
    logger_config.info(f"command to run {cmd}")


    result = subprocess.run(["bash", "-c", cmd], cwd=cwd, text=True, env=config.SUBPROCESS_ENV)
    if result.returncode != 0:
        raise ValueError(f"FaceTagger failed with code {result.returncode}")
