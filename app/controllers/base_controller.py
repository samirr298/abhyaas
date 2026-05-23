from flask import render_template, redirect, url_for, flash, session


class BaseController:
	

	# Provides `render`, `redirect_to`, `flash` and `session` helpers so
	# child controllers stay concise.

	def render(self, template_name, **context):
		return render_template(template_name, **context)

	def redirect_to(self, endpoint, **values):
		return redirect(url_for(endpoint, **values))

	def flash(self, message, category='info'):
		flash(message, category)

	@property
	def session(self):
		return session

