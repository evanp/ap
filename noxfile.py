import nox


@nox.session
def tests(session):
    session.run("poetry", "install")
    session.run("python", "-m", "unittest", "discover", "-s", "tests")


@nox.session
def install_global(session):
    session.run("poetry", "build")
    session.run("poetry", "install", "--no-root")
