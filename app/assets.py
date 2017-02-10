from flask_assets import Bundle

app_css = Bundle('*.scss', filters='scss', output='css/app.css')

app_js = Bundle('app.js', filters='jsmin', output='js/app.js')

vendor_css = Bundle('vendor/*.css', 'vendor/components/*.css', output='css/vendor.css')

vendor_js = Bundle('vendor/*.js', 'vendor/components/*.js', filters='jsmin', output='js/vendor.js')
