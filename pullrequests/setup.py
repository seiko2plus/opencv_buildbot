from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from buildbot_pkg import setup_www_plugin
except ImportError:
    import sys
    print("Please install buildbot_pkg module in order to install that package, or use the pre-build .whl modules available on pypi", file=sys.stderr)
    sys.exit(1)

setup_www_plugin(
    name='opencv-pullrequests',
    description='OpenCV pullrequests',
    author=u'OpenCV Team Members',
    author_email=u'seiko@imavr.com',
    url='https://opencv.org',
    license='GNU GPL',
    packages=['opencv_pullrequests'],
    install_requires=[
        'klein'
    ],
    package_data={
        '': [
            'VERSION',
            'static/*'
        ],
    },
    entry_points="""
        [buildbot.www]
        pullrequests = opencv_pullrequests:ep
    """,
)