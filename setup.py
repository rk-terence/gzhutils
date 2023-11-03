from setuptools import Extension, setup


setup(
    ext_modules=[
        Extension(
            name="gzhutils._printf",
            sources=["src/gzhutils/_printfmodule.c"],
        )
    ],
    include_package_data=True,
    package_data={
        'gzhutils': ['_printf.pyi']
    }
)
