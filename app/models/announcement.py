from app.models.base_model import BaseModel

class Announcement(BaseModel):
    
    @classmethod
    def add_announcement(cls, title,short_description, category,user_id,full_description):
        sql = "insert into announcements(title,summary,category,author_id,body) values(%s,%s,%s,%s,%s)"
        return cls.execute_write(sql, [title,short_description, category,user_id,full_description])
    @classmethod
    def get_annoucement(cls, offset, perpage):
        """Counts total days for a specific status ('present' or 'absent')."""
        sql = "SELECT a.*, u.name AS author_name FROM announcements a JOIN users u ON a.author_id = u.id ORDER BY a.created_at DESC  LIMIT %s OFFSET %s"
        result = cls.fetch_all(sql, [perpage,offset])
        return result if result else []
    
    @classmethod
    def get_total_annoucement_count(cls):
        """Counts total days for a specific status ('present' or 'absent')."""
        sql = "SELECT count(*) as count FROM announcements "
        result = cls.fetch_one(sql)
        return result['count'] if result else 0
    @classmethod
    def get_annoucement_byid(cls,anid):
        sql = "SELECT a.*, u.name AS author_name FROM announcements a JOIN users u ON a.author_id = u.id WHERE a.id = %s"
        result = cls.fetch_one(sql, [anid])
        return result if result else 0
