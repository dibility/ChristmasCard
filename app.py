from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# 프로젝트 루트 디렉토리 설정
basedir = os.path.abspath(os.path.dirname(__file__))

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'christmas_cards.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')

# 업로드 폴더가 없다면 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

class ChristmasCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200))
    password_hash = db.Column(db.String(200), nullable=False)  # 비밀번호 해시 추가
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 데이터베이스 초기화 함수
def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized!")

@app.route('/')
def index():
    cards = ChristmasCard.query.order_by(ChristmasCard.created_at.desc()).all()
    return render_template('index.html', cards=cards)

@app.route('/write', methods=['GET'])
def write_form():
    return render_template('write.html')

@app.route('/write', methods=['POST'])
def write():
    author = request.form['author']
    message = request.form['message']
    password = request.form['password']  # 비밀번호 받기
    image = request.files['image']
    
    image_path = ''
    if image and image.filename:
        # 파일명을 안전하게 만들기
        from werkzeug.utils import secure_filename
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}")
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f"uploads/{filename}"
    
    new_card = ChristmasCard(
        author=author,
        message=message,
        image_path=image_path
    )
    new_card.set_password(password)  # 비밀번호 설정
    
    db.session.add(new_card)
    db.session.commit()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)