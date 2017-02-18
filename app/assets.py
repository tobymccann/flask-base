from flask_assets import Bundle

app_css = Bundle('app.scss', filters='scss', output='css/app.css')

app_js = Bundle('app.js', filters='jsmin', output='js/app.js')

vendor_css = Bundle('vendor/semantic.css', 'vendor/components/*.css', output='css/vendor.css')

vendor_js = Bundle('vendor/jquery-3.1.1.js', 'vendor/semantic.min.js', 'vendor/jquery.tablesort.js',
                   'vendor/zxcvbn.js', 'vendor/*.js', filters='jsmin', output='scripts/vendor.js')
