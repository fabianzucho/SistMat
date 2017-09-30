# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
import logging
import werkzeug
import openerp
from openerp.addons.auth_signup.res_users import SignupError
from openerp.addons.web.controllers.main import ensure_db
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, ustr

_logger = logging.getLogger(__name__)

class AuthSignupHome(openerp.addons.web.controllers.main.Home):
	_cp_path = '/auth_iaen'

	def do_signup(self, qcontext):
		values = dict((key, qcontext.get(key)) for key in ('login', 'password', 'name','tip_identification','email','tip_register'))
		assert any([k for k in values.values()]), "The form was not properly filled in."
		assert values.get('password') == qcontext.get('confirm_password'), "Error: Las contraseñas no coinciden, por favor verificar !"
		if qcontext.get('token'):
			return super(AuthSignupHome, self).do_signup(qcontext)
		else:
			mensaje = ""
			try:
				tipo = values.get('tip_identification')
				if (tipo == 'C'):
					res = self.validate_identification(values.get('login'))
				else:
					res = True
				if (res == True):
					if values.get('tip_register') == 'E':
						data = {'email': values.get('email'),'identification': values.get('login'),'tip_identification' : values.get('tip_identification'),'name' : ' '}
						student_exists = user = request.registry['siaad.student'].search(request.cr, openerp.SUPERUSER_ID,[('identification','=', values.get('login'))])
						if student_exists :
							mensaje = "Error: Usuario ya existe en el sistema !"
							raise SignupError("")
						else :
							alumno_id = request.registry['siaad.student'].create(request.cr, openerp.SUPERUSER_ID, data, {"password": values.get('password')})
							request.cr.commit()
							alumn_obj = request.registry['siaad.student'].browse(request.cr, openerp.SUPERUSER_ID, alumno_id)
							user_id = request.registry['res.users'].search(request.cr, openerp.SUPERUSER_ID,[('partner_id','=',alumn_obj.partner_id.id)])
							request.registry['res.partner'].write(request.cr, openerp.SUPERUSER_ID, alumn_obj.partner_id.id, {'user_id' : user_id[0]})
							user = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD user')])
							estudiantes = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD Estudiantes')])
							sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(user[0],user_id[0])
							request.cr.execute(sql)
							sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(estudiantes[0],user_id[0])
							request.cr.execute(sql)
							res = {'res_model': 'siaad.student', 'res_id': alumno_id, 'partner_id': alumn_obj.partner_id.id}
							request.cr.commit()

					elif values.get('tip_register') == 'D':
						data = {'email': values.get('email'),'identification': values.get('login'),'tip_identification' : values.get('tip_identification'),'name' : values.get('email'),'register' : 'formulario'}
						teaching_id = request.registry['siaad.teaching'].create(request.cr, openerp.SUPERUSER_ID, data, {"password": values.get('password')})
						request.cr.commit()
						teaching_obj = request.registry['siaad.teaching'].browse(request.cr, openerp.SUPERUSER_ID, teaching_id)
						user_id = request.registry['res.users'].search(request.cr, openerp.SUPERUSER_ID,[('partner_id','=',teaching_obj.partner_id.id)])
						request.registry['res.partner'].write(request.cr, openerp.SUPERUSER_ID, teaching_obj.partner_id.id, {'user_id' : user_id[0]})
						user = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD user')])
						docentes = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD Docente')])
						sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(user[0],user_id[0])
						request.cr.execute(sql)
						sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(docentes[0],user_id[0])
						request.cr.execute(sql)
						res = {'res_model': 'siaad.teaching', 'res_id': teaching_id, 'partner_id': teaching_obj.partner_id.id}
						request.cr.commit()
					elif values.get('tip_register') == 'G':
						user_obj = request.registry['res.users'].search(request.cr,openerp.SUPERUSER_ID,[('login', '=', values.get('login'))])
						if len(user_obj) > 0:
							group_graduado_obj = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD Estudiante Graduado')])
							sql = "SELECT * FROM res_groups_users_rel WHERE uid=%s AND gid =%s"%(user_obj[0], group_graduado_obj[0])
							request.cr.execute(sql)
							res_group_graduado_obj = request.cr.fetchall()
							group_estudiante_obj = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD Estudiantes')])
							sql = "SELECT * FROM res_groups_users_rel WHERE uid=%s AND gid =%s"%(user_obj[0], group_estudiante_obj[0])
							request.cr.execute(sql)
							res_group_estudiante_obj = request.cr.fetchall()
							if len(res_group_graduado_obj) == 0:
								sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(group_graduado_obj[0],user_obj[0])
								request.cr.execute(sql)
								request.cr.commit()
							if len(res_group_estudiante_obj) == 0:
								sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(group_estudiante_obj[0],user_obj[0])
								request.cr.execute(sql)
								request.cr.commit()
							partner_obj = request.registry['res.partner'].search(request.cr, openerp.SUPERUSER_ID,[('user_id','=',user_obj[0])])
							sql = "update siaad_student set student_graduate = %s where partner_id = %s "%(True, partner_obj[0])
							request.cr.execute(sql)
						else :
							data = {'email': values.get('email'),'identification': values.get('login'),'tip_identification' : values.get('tip_identification'),'name' : values.get('email')}
							alumno_id = request.registry['siaad.student'].create(request.cr, openerp.SUPERUSER_ID, data, {"password": values.get('password')})
							request.cr.commit()
							alumn_obj = request.registry['siaad.student'].browse(request.cr, openerp.SUPERUSER_ID, alumno_id)
							user_id = request.registry['res.users'].search(request.cr, openerp.SUPERUSER_ID,[('partner_id','=',alumn_obj.partner_id.id)])
							request.registry['res.partner'].write(request.cr, openerp.SUPERUSER_ID, alumn_obj.partner_id.id, {'user_id' : user_id[0]})
							user = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD user')])
							estudiantes = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD Estudiantes')])
							graduado = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID,[('name','ilike','SIAAD Estudiante Graduado')])
							sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(user[0],user_id[0])
							request.cr.execute(sql)
							sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(estudiantes[0],user_id[0])
							request.cr.execute(sql)
							sql = "insert into res_groups_users_rel (gid, uid) values (%s, %s)"%(graduado[0],user_id[0])
							request.cr.execute(sql)
							sql = "update siaad_student set student_graduate = %s where id = %s "%(True, alumn_obj.id)
							request.cr.execute(sql)
							res = {'res_model': 'siaad.student', 'res_id': alumno_id, 'partner_id': alumn_obj.partner_id.id}
							request.cr.commit()
				else:
					mensaje = "Error: Cédula es incorrecta !"
					raise SignupError("")

			except Exception, e:
				raise SignupError(mensaje)

	def validate_identification(self,identification):
		sumatory = 0
		result = 0
		if len(identification) != 10 :
			return False

		for i in range(0, len(identification)-1):
			if i % 2 == 0:
				result = int(identification[i])*2
			else:
				result = int(identification[i])*1

			if result > 9:
				result = int(str(result)[0]) + int(str(result)[1])

			sumatory += result

		if (sumatory % 10 == 0 and identification[len(identification)-1]=='0') or 10 - (sumatory % 10) == int(identification[len(identification)-1]):
			return True
		else:
			return False
