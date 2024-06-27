import setuptools

with open('requirements.txt', 'r') as f:
    install_requires = (req[0] for req in map(lambda x: x.split('#'), f.readlines()))
    install_requires = [req for req in map(str.strip, install_requires) if req]

with open("README.md", "r", encoding="utf-8") as file:
    long_description = file.read()

setuptools.setup(
    name="pynball_rl",
    author="Tom Smith",
    version="0.0.1",
    python_requires=">=3.9",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    description="A python implementation of the classic reinforcement learning domain pinball: http://irl.cs.brown.edu/pinball/",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
