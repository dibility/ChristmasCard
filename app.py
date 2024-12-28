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

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('christmas_card.id', ondelete='CASCADE'), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

@app.route('/comment/<int:card_id>', methods=['POST'])
def add_comment(card_id):
    card = ChristmasCard.query.get_or_404(card_id)
    author = request.form['comment_author']
    content = request.form['comment_content']
    password = request.form['comment_password']

    new_comment = Comment(
        card_id=card_id,
        author=author,
        content=content
    )
    new_comment.set_password(password)

    db.session.add(new_comment)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    password = request.form['comment_password']
    
    if comment.check_password(password):
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return "비밀번호가 올바르지 않습니다.", 403

@app.route('/delete/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    card = ChristmasCard.query.get_or_404(card_id)
    password = request.form['password']
    if card.check_password(password):
        db.session.delete(card)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return "비밀번호가 올바르지 않습니다.", 403
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)