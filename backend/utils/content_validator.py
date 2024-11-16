class ContentValidator:
    @staticmethod
    def validate_slide_content(slide_content):
        """Validate the content for a slide"""
        if not isinstance(slide_content, dict):
            raise ValueError("Slide content must be a dictionary")
        
        if 'title' not in slide_content:
            raise ValueError("Slide must have a title")
        
        if 'content' not in slide_content:
            raise ValueError("Slide must have content")
        
        if not isinstance(slide_content['content'], list):
            raise ValueError("Slide content must be a list")
        
        # Ensure content isn't too long
        from config import Config
        
        if len(slide_content['content']) > Config.MAX_POINTS_PER_SLIDE:
            slide_content['content'] = slide_content['content'][:Config.MAX_POINTS_PER_SLIDE]
        
        # Truncate long points
        slide_content['content'] = [
            point[:Config.MAX_POINT_LENGTH] + '...' if len(point) > Config.MAX_POINT_LENGTH else point
            for point in slide_content['content']
        ]
        
        return slide_content