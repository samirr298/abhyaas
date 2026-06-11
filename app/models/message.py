from app.models.base_model import BaseModel

class Messagemodel(BaseModel):
    
    @classmethod
    def get_all_teacher(cls,):
        """Fetches all teacher records."""
        sql = "SELECT * from users where role = 'teacher'"
        return cls.fetch_all(sql)
