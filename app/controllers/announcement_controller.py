from flask import render_template, request,redirect,url_for,flash
from app.controllers.base_controller import BaseController
from app.models.announcement import Announcement
import math
class AnnouncementController(BaseController):
    def announcement(self):
        # Showing the annoucements now 
        page = request.args.get('page',default=1,type = int)
        perpage = 10
        offset = (page - 1) * perpage
        annoucementshistory = Announcement.get_annoucement(offset,perpage)
        unique_categories = set(rec['category'] for rec in annoucementshistory)
        total_rows = Announcement.get_total_annoucement_count()
        total_pages = math.ceil(total_rows / perpage) if total_rows > 0 else 1
        print(unique_categories)
        print(total_pages)
        print(total_rows)
        return self.render(
            'announcement/announcement.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            show = "all",
            unique_categories = unique_categories,
            annoucementshistory=annoucementshistory,      # <--- Passed to HTML table loop
            current_page=page,            # <--- Passed for active page color
            total_pages=total_pages
             
            
        )
    def name(self):
        print("name")
    def announcement_view(self,announcement_id):
       annoucementshistory = Announcement.get_annoucement_byid(announcement_id)
       return self.render(
            'announcement/announcementview.html',
           
            annoucementshistory=annoucementshistory   # <--- Passed to HTML table loop
            
            
            
        )

    def announcement_create(self):
        if request.method == "POST":
            title = request.form.get('title')
            category = request.form.get('category')
            short_description = request.form.get('summary')
            full_description = request.form.get('description')
            user_id =self.session.get('user_id')
            

            if not title or not category or not short_description or not full_description:
                return self.render(
                    'announcement/announcement.html',
                    username=self.session.get('username'),
                    email=self.session.get('email'),
                    role=self.session.get('role'),
                    
                    annoucementshistory=[],
                    current_page=1,
                    total_pages=1
                )

            result = Announcement.add_announcement(title,short_description, category,user_id,full_description)
            if result:
                flash("Succesfully added the annoucements !",'success')
            else:
                flash("Can't add the annoucements !",'error')
            return redirect(url_for('announce.announcement'))
            print('done')

        # Showing twdhe annoucements now 
       
        return self.render(
            'announcement/announcement.html',
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            send='renderthepage',
            show = "all",
            annoucementshistory=[],
            current_page=1,
            total_pages=1
        )
    def annoucement_category(self,category):
        page = request.args.get('page',default=1,type = int)
        perpage = 10
        offset = (page - 1) * perpage
        annoucementshistory = Announcement.get_annoucement(offset,perpage)
        unique_categories = set(rec['category'] for rec in annoucementshistory)
        total_rows = Announcement.get_total_annoucement_count()
        total_pages = math.ceil(total_rows / perpage) if total_rows > 0 else 1
        print(unique_categories)
        print(total_pages)
        print(total_rows)
        return self.render(
            'announcement/announcementcategory.html',
            categories = category,
            username=self.session.get('username'),
            email=self.session.get('email'),
            role=self.session.get('role'),
            show = "all",
            unique_categories = unique_categories,
            annoucementshistory=annoucementshistory,      # <--- Passed to HTML table loop
            current_page=page,            # <--- Passed for active page color
            total_pages=total_pages
            
            
        )