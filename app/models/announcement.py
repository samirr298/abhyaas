from app.models.base_model import BaseModel

class Announcement(BaseModel):
    """
    Announcement Model
    
    Handles database interactions for the system's announcement feature.
    Optimized for repository presentation and clean query execution.
    """
    
    @classmethod
    def add_announcement(cls, title, short_description, category, user_id, full_description):
        """Inserts a new announcement record into the database."""
        sql = "INSERT INTO announcements(title, summary, category, author_id, body) VALUES (%s, %s, %s, %s, %s)"
        return cls.execute_write(sql, [title, short_description, category, user_id, full_description])
        
    @classmethod
    def get_annoucement(cls, offset, perpage):
        """Retrieves a paginated list of announcements with author details, sorted by latest."""
        sql = """
            SELECT a.*, u.name AS author_name 
            FROM announcements a 
            JOIN users u ON a.author_id = u.id 
            ORDER BY a.created_at DESC  
            LIMIT %s OFFSET %s
        """
        result = cls.fetch_all(sql, [perpage, offset])
        return result if result else []
    
    @classmethod
    def get_total_annoucement_count(cls):
        """Returns the total number of announcements available in the database."""
        sql = "SELECT COUNT(*) AS count FROM announcements"
        result = cls.fetch_one(sql)
        return result['count'] if result else 0
        
    @classmethod
    def get_annoucement_byid(cls, anid):
        """Fetches a specific announcement entry by its primary key ID."""
        sql = """
            SELECT a.*, u.name AS author_name 
            FROM announcements a 
            JOIN users u ON a.author_id = u.id 
            WHERE a.id = %s
        """
        result = cls.fetch_one(sql, [anid])
        return result if result else 0