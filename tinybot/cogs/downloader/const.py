class Git:
    clone = "git clone -c credential.helper= -c core.askpass= --recurse-submodules -b {branch} {url} {folder}"
    clone_no_branch = (
        "git -c credential.helper= -c core.askpass= clone --recurse-submodules {url} {folder}"
    )
    current_branch = "git -C {path} symbolic-ref --short HEAD"
    current_commit = "git -C {path} rev-parse HEAD"
    latest_commit = "git -C {path} rev-parse {branch}"
    hard_reset = "git -C {path} reset --hard origin/{branch} -q"
    pull = "git -c credential.helper= -c core.askpass= -C {path} pull --recurse-submodules -q --ff-only"
    diff_file_status = "git -C {path} diff-tree --no-commit-id --name-status -r -z --line-prefix='\t' {old_rev} {new_rev}"
    log = "git -C {path} log --relative-date --reverse {old_rev}.. {relative_file_path}"
    remote_url = "git -C {path} config --get remote.origin.url"
    checkout = "git -C {path} checkout {rev}"
    pip_install = "{python} -m pip install -U -t {target_dir} {reqs}"
