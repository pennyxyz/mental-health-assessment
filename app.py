import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import sys
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "submissions.json")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(
    page_title="心理健康评估系统",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    defaults = {
        'current_questionnaire': None,
        'questionnaire_responses': {'CDRISC': {}, 'CPSS': {}, 'CSQ': {}, 'SCL90': {}},
        'questionnaire_scores': {'CDRISC': None, 'CPSS': None, 'CSQ': None, 'SCL90': None},
        'questionnaire_completed': {'CDRISC': False, 'CPSS': False, 'CSQ': False, 'SCL90': False},
        'assessment_result': None,
        'show_success_message': False,
        'user_info': {},
        'submission_id': None,
        'admin_mode': False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    if not st.session_state.submission_id:
        st.session_state.submission_id = str(uuid.uuid4())[:8]

init_session_state()

QUESTIONNAIRES = {
    'CDRISC': {
        'name': '心理韧性量表 CD-RISC',
        'description': '请根据你的实际情况，选择最符合的选项（0=从来不，1=很少，2=有时，3=经常，4=一直如此）',
        'scale': '0-4分 (0=从来不，1=很少，2=有时，3=经常，4=一直如此)',
        'questions': [
            "1. 我能适应变化", "2. 我有让我感到亲密、安全的关系", "3. 有时，命运或神灵能帮忙",
            "4. 无论发生什么我都能应付", "5. 过去的成功让我有信心面对挑战", "6. 我能看到事情幽默的一面",
            "7. 应对压力使我感到有力量", "8. 经历艰难或疾病后，我往往会很快恢复", "9. 认为事情发生总是有原因的",
            "10. 无论结果怎样，我都会尽自己最大的努力", "11. 我能实现自己的目标", "12. 当事情看起来没什么希望时，我不会轻易放弃",
            "13. 我知道去哪里寻找帮助", "14. 在压力下，我能够集中注意力并清晰思考", "15. 我喜欢在解决问题时起带头作用",
            "16. 我不会因失败而气馁", "17. 我认为自己是个强有力的人", "18. 我能做出不寻常的或艰难的决定",
            "19. 我能处理不快乐的情绪", "20. 不知道事情如何处理时我会按照预感行事", "21. 我有强烈的目的感",
            "22. 我感觉能掌控自己的生活", "23. 我喜欢挑战", "24. 我努力工作以达到目标", "25. 我对自己的成绩感到骄傲"
        ],
        'reverse_items': [],
        'factorKey': {'tough': [11,12,13,14,15,16,17,18,19,20,21,22,23],
                     'strength': [1,5,7,8,9,10,24,25],
                     'optimism': [2,3,4,6]},
        'score_ranges': {'very_bad': (0, 25), 'bad': (26, 50), 'good': (51, 75), 'very_good': (76, 100)},
        'factor_levels': {
            'tough': {"0-13":"极差","14-26":"较差","27-39":"较好","40-52":"非常好"},
            'strength': {"0-8":"极差","9-16":"较差","17-24":"较好","25-32":"非常好"},
            'optimism': {"0-4":"极差","5-8":"较差","9-12":"较好","13-16":"非常好"}
        }
    },
    'CPSS': {
        'name': '压力知觉量表 CPSS',
        'description': '请根据你的实际感受，选择最符合的选项（1=从不，2=偶尔，3=有时，4=经常，5=总是）',
        'scale': '1-5分 (1=从不，2=偶尔，3=有时，4=经常，5=总是)',
        'questions': [
            "1. 为一些无法预期的事情的发生而感到心烦意乱", "2. 感觉无法控制生活中重要的事情",
            "3. 感到紧张不安和压力", "4. 成功的处理恼人的生活烦恼",
            "5. 感到自己能有效地处理生活中所发生的重要改变", "6. 对于有能力处理自己的私人问题感到很有信心",
            "7. 感到事情顺心如意", "8. 发现自己无法处理所有自己必须做的事情",
            "9. 有办法控制生活中恼人的事情", "10. 常觉得自己是驾驭事情的主人",
            "11. 经常生气，因为很多事情的发生是超出自己所能控制的", "12. 经常想到有些事情是自己必须完成的",
            "13. 常能掌握时间的安排方式", "14. 常感到困难的事情堆积如山，而自己无法克服它们"
        ],
        'reverse_items': [4,5,6,7,9,10,13],
        'score_ranges': {'low': (14, 28), 'medium': (29, 42), 'high': (43, 56), 'very_high': (57, 70)}
    },
    'CSQ': {
        'name': '应急处置应对方式 CSQ',
        'description': '请根据你的行为习惯，选择最符合的选项（0=不采取，1=偶尔采取，2=有时采取，3=经常采取）',
        'scale': '0-3分 (0=不采取，1=偶尔采取，2=有时采取，3=经常采取)',
        'questions': [
            "1. 通过工作学习或一些其他活动解脱", "2. 与人交谈，倾诉内心烦恼", "3. 尽量看到事物好的一面",
            "4. 改变自己的想法，重新发现生活中什么重要", "5. 不把问题看得太严重", "6. 坚持自己的立场，为自己想得到的斗争",
            "7. 找出几种不同的解决问题的方法", "8. 向亲戚朋友或同学寻求建议", "9. 改变原来的一些做法或自己的一些问题",
            "10. 借鉴他人处理类似困难情景的办法", "11. 寻求业余爱好，积极参加文体活动",
            "12. 尽量克制自己的失望、悔恨、悲伤和愤怒感情", "13. 试图休息或休假，暂时把问题(烦恼)抛开",
            "14. 通过吸烟、喝酒、服药和吃东西来解除烦恼", "15. 认为时间会改变现状，唯一要做的便是等待",
            "16. 试图忘记整个事情", "17. 依靠别人解决问题", "18. 接受现实，因为没有其它办法",
            "19. 幻想可能会发生某种奇迹改变现状", "20. 自己安慰自己"
        ],
        'reverse_items': [],
        'factorKey': {'positive': [1,2,3,4,5,6,7,8,9,10,11,12],
                     'negative': [13,14,15,16,17,18,19,20]},
        'score_ranges': {}
    },
    'SCL90': {
        'name': '症状自评量表 SCL-90',
        'description': '请根据你最近一周的实际感受，选择最符合的选项（1=没有，2=很轻，3=中等，4=偏重，5=严重）',
        'scale': '1-5分 (1=没有，2=很轻，3=中等，4=偏重，5=严重)',
        'questions': [
            "1. 头痛","2. 神经过敏，心中不踏实","3. 头脑中有不必要的想法或字句盘旋","4. 头昏或昏倒","5. 对异性的兴趣减退",
            "6. 对旁人责备求全","7. 感到别人能控制您的思想","8. 责怪别人制造麻烦","9. 忘记性大","10. 担心自己的衣饰整齐及仪态的端正",
            "11. 容易烦恼和激动","12. 胸痛","13. 害怕空旷的场所或街道","14. 感到自己的精力下降，活动减慢","15. 想结束自己的生命",
            "16. 听到旁人听不到的声音","17. 发抖","18. 感到大多数人都不可信任","19. 胃口不好","20. 容易哭泣",
            "21. 同异性相处时感到害羞不自在","22. 感到受骗，中了圈套或有人想抓住您","23. 无缘无故地突然感到害怕","24. 自己不能控制地大发脾气","25. 怕单独出门",
            "26. 经常责怪自己","27. 腰痛","28. 感到难以完成任务","29. 感到孤独","30. 感到苦闷",
            "31. 过分担忧","32. 对事物不感兴趣","33. 感到害怕","34. 感到您的感情容易受到伤害","35. 旁人能知道您的私下想法",
            "36. 感到别人不理解您、不同情您","37. 感到人们对您不友好、不喜欢您","38. 做事必须做得很慢以保证做得正确","39. 心跳得很厉害","40. 恶心或胃部不舒服",
            "41. 感到比不上他人","42. 肌肉酸痛","43. 感到有人在监视您、谈论您","44. 难以入睡","45. 做事必须反复检查",
            "46. 难以作出决定","47. 怕乘电车、公共汽车、地铁或火车","48. 呼吸有困难","49. 一阵阵发冷或发热","50. 因为感到害怕而避开某些东西、场合或活动",
            "51. 脑子变空了","52. 身体发麻或刺痛","53. 喉咙有梗塞感","54. 感到前途没有希望","55. 不能集中注意力",
            "56. 感到身体的某一部分软弱无力","57. 感到紧张或容易紧张","58. 感到手或脚发重","59. 想到死亡的事","60. 吃得太多",
            "61. 当别人看着您或谈论您时感到不自在","62. 有一些不属于您自己的想法","63. 有想打人或伤害他人的冲动","64. 醒得太早","65. 必须反复洗手、点数或触摸某些东西",
            "66. 睡得不稳不深","67. 有想摔坏或破坏东西的冲动","68. 有一些别人没有的想法或念头","69. 感到对别人神经过敏","70. 在商店或电影院等人多的地方感到不自在",
            "71. 感到任何事情都很困难","72. 一阵阵恐惧或惊恐","73. 感到在公共场合吃东西很不舒服","74. 经常与人争论","75. 单独一人时神经很紧张",
            "76. 别人对您的成绩没有作出恰当的评价","77. 即使和别人在一起也感到孤单","78. 感到坐立不安心神不定","79. 感到自己没有什么价值","80. 感到熟悉的东西变成陌生或不像真的",
            "81. 大叫或摔东西","82. 害怕会在公共场合昏倒","83. 感到别人想占您的便宜","84. 为一些有关性的想法而很苦恼","85. 您认为应该因为自己的过错而受到惩罚",
            "86. 感到要很快把事情做完","87. 感到自己的身体有严重问题","88. 从未感到和其他人很亲近","89. 感到自己有罪","90. 感到自己的脑子有毛病"
        ],
        'reverse_items': [],
        'factorKey': {
            'soma': [1,4,12,27,40,42,48,49,52,53,56,58], 'obsess': [3,9,10,28,38,45,46,51,55,65],
            'inter': [6,21,34,36,37,41,61,69,73], 'depress': [5,14,15,20,22,26,29,30,31,32,54,71,79],
            'anx': [2,17,23,33,39,57,72,78,80,86], 'host': [11,24,63,67,74,81], 'phob': [13,25,47,50,70,75,82],
            'paran': [8,18,43,68,76,83], 'psycho': [7,16,35,62,77,84,85,87,88,90], 'other': [19,44,59,60,64,66,89]
        },
        'score_ranges': {
            'no_symptom': (1.0, 1.5), 'mild': (1.5, 2.5), 'moderate': (2.5, 3.5),
            'severe': (3.5, 4.5), 'very_severe': (4.5, 5.0)
        },
        'positiveCut': {'total': 160, 'posNum': 43, 'factor': 2.0}
    }
}

def calculate_cdrisc_score(responses):
    total = 0
    factor_scores = {'tough':0, 'strength':0, 'optimism':0}
    for i in range(1, 26):
        if i in responses: total += responses[i]
    factor_key = QUESTIONNAIRES['CDRISC']['factorKey']
    for factor, item_nums in factor_key.items():
        for num in item_nums:
            if num in responses: factor_scores[factor] += responses[num]
    return {'total': total, 'factors': factor_scores}

def calculate_cpss_score(responses):
    total = 0
    reverse_items = QUESTIONNAIRES['CPSS']['reverse_items']
    for i in range(1, 15):
        if i in responses:
            score = responses[i]
            total += (6 - score) if i in reverse_items else score
    return total

def calculate_csq_score(responses):
    factor_scores = {'positive':0, 'negative':0}
    factor_key = QUESTIONNAIRES['CSQ']['factorKey']
    for factor, item_nums in factor_key.items():
        for num in item_nums:
            if num in responses: factor_scores[factor] += responses[num]
    pos, neg = factor_scores['positive'], factor_scores['negative']
    if pos > neg: style = "解决者"
    elif neg > pos: style = "承受者"
    elif pos == neg and pos > 9: style = "矛盾者"
    else: style = "疏离者"
    return {'factors': factor_scores, 'style': style}

def calculate_scl90_score(responses):
    total = 0; pos_num = 0; factor_scores = {}
    factor_key = QUESTIONNAIRES['SCL90']['factorKey']
    for factor in factor_key: factor_scores[factor] = 0.0
    for i in range(1, 91):
        if i in responses:
            score = responses[i]; total += score
            if score >= 2: pos_num += 1
    for factor, item_nums in factor_key.items():
        item_total = 0; valid_count = 0
        for num in item_nums:
            if num in responses: item_total += responses[num]; valid_count += 1
        if valid_count > 0: factor_scores[factor] = round(item_total / valid_count, 2)
    return {'total': total, 'posNum': pos_num, 'factors': factor_scores}

def save_submission():
    if not all(st.session_state.questionnaire_completed.values()):
        return False
    
    submission = {
        'submission_id': st.session_state.submission_id,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user_info': st.session_state.user_info,
        'questionnaire_responses': st.session_state.questionnaire_responses,
        'questionnaire_scores': st.session_state.questionnaire_scores,
        'assessment_result': st.session_state.assessment_result
    }
    
    existing_data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        existing_data.append(json.loads(line.strip()))
        except:
            existing_data = []
    
    existing_data.append(submission)
    
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            for item in existing_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False

def load_all_submissions():
    if not os.path.exists(DATA_FILE):
        return []
    
    try:
        submissions = []
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    submissions.append(json.loads(line.strip()))
        return submissions
    except Exception as e:
        st.error(f"读取数据失败: {e}")
        return []

def export_to_excel():
    submissions = load_all_submissions()
    if not submissions:
        return None
    
    rows = []
    for sub in submissions:
        row = {
            '提交ID': sub['submission_id'],
            '提交时间': sub['timestamp'],
            '姓名': sub['user_info'].get('name', ''),
            '编号': sub['user_info'].get('code', ''),
            '备注': sub['user_info'].get('note', ''),
        }
        
        scores = sub['questionnaire_scores']
        if scores['CDRISC']:
            row['CDRISC总分'] = scores['CDRISC']['total']
            row['CDRISC坚韧'] = scores['CDRISC']['factors']['tough']
            row['CDRISC力量'] = scores['CDRISC']['factors']['strength']
            row['CDRISC乐观'] = scores['CDRISC']['factors']['optimism']
        
        if scores['CPSS']:
            row['CPSS总分'] = scores['CPSS']
        
        if scores['CSQ']:
            row['CSQ类型'] = scores['CSQ']['style']
            row['CSQ积极'] = scores['CSQ']['factors']['positive']
            row['CSQ消极'] = scores['CSQ']['factors']['negative']
        
        if scores['SCL90']:
            row['SCL90总分'] = scores['SCL90']['total']
            row['SCL90阳性项目'] = scores['SCL90']['posNum']
        
        if sub['assessment_result']:
            row['综合风险等级'] = sub['assessment_result']['overall_risk']
            row['风险点数'] = sub['assessment_result']['risk_points']
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df

def show_user_info_form():
    st.header("个人信息")
    st.write("请在开始评估前填写以下信息（可选）")
    
    with st.form(key="user_info_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("姓名", value=st.session_state.user_info.get('name', ''))
        with col2:
            code = st.text_input("编号/学号", value=st.session_state.user_info.get('code', ''))
        
        note = st.text_area("备注（可选）", value=st.session_state.user_info.get('note', ''))
        
        if st.form_submit_button("保存信息并开始评估"):
            if name.strip() or code.strip():
                st.session_state.user_info = {
                    'name': name.strip(),
                    'code': code.strip(),
                    'note': note.strip()
                }
                st.success("信息已保存！您现在可以开始填写问卷。")
                st.rerun()
            else:
                st.warning("至少填写姓名或编号中的一项")

def show_admin_panel():
    st.title("📊 数据管理面板")
    
    if not st.session_state.admin_mode:
        password = st.text_input("请输入管理员密码", type="password")
        if st.button("登录"):
            if password == "admin123":
                st.session_state.admin_mode = True
                st.rerun()
            else:
                st.error("密码错误")
        return
    
    st.success("✅ 管理员模式已启用")
    
    submissions = load_all_submissions()
    
    if not submissions:
        st.info("暂无提交数据")
        return
    
    st.subheader(f"📈 数据概览（共 {len(submissions)} 条记录）")
    
    df = export_to_excel()
    if df is not None:
        st.dataframe(df, use_container_width=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总提交数", len(submissions))
        with col2:
            cdrisc_avg = df['CDRISC总分'].mean() if 'CDRISC总分' in df.columns else 0
            st.metric("CDRISC平均分", f"{cdrisc_avg:.1f}")
        with col3:
            cpss_avg = df['CPSS总分'].mean() if 'CPSS总分' in df.columns else 0
            st.metric("CPSS平均分", f"{cpss_avg:.1f}")
        with col4:
            risk_counts = df['综合风险等级'].value_counts() if '综合风险等级' in df.columns else {}
            st.metric("高风险数", risk_counts.get('red', 0))
    
    st.subheader("📤 数据导出")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("导出为Excel文件"):
            df = export_to_excel()
            if df is not None:
                excel_data = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="下载Excel文件",
                    data=excel_data,
                    file_name=f"心理评估数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("导出原始JSON数据"):
            submissions = load_all_submissions()
            if submissions:
                json_data = json.dumps(submissions, ensure_ascii=False, indent=2)
                st.download_button(
                    label="下载JSON数据",
                    data=json_data,
                    file_name=f"心理评估原始数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    st.subheader("🔍 详细数据查看")
    if submissions:
        selected_id = st.selectbox(
            "选择要查看的提交记录",
            options=[f"{s['submission_id']} - {s['user_info'].get('name', '匿名')} ({s['timestamp']})" 
                    for s in submissions]
        )
        
        if selected_id:
            selected_index = [f"{s['submission_id']} - {s['user_info'].get('name', '匿名')} ({s['timestamp']})" 
                             for s in submissions].index(selected_id)
            selected_submission = submissions[selected_index]
            
            with st.expander("查看详细数据"):
                st.json(selected_submission)
    
    st.subheader("🧹 数据管理")
    if st.button("清空所有数据（谨慎操作）"):
        if st.checkbox("确认要清空所有数据吗？此操作不可恢复"):
            try:
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                    st.success("数据已清空")
                    st.rerun()
            except Exception as e:
                st.error(f"清空失败: {e}")
    
    if st.button("退出管理员模式"):
        st.session_state.admin_mode = False
        st.rerun()

def show_questionnaire(questionnaire_id):
    q_info = QUESTIONNAIRES[questionnaire_id]
    st.header(q_info['name'])
    st.write(q_info['description'])
    st.write(f"**评分标准：** {q_info['scale']}")
    
    if st.session_state.get('show_success_message'):
        st.success(f"🎉 {q_info['name']} 问卷已提交成功！")
        st.session_state.show_success_message = False
        
        score = st.session_state.questionnaire_scores[questionnaire_id]
        if score:
            if questionnaire_id == 'CDRISC':
                st.info(f"总分：{score['total']} (坚韧：{score['factors']['tough']}, 力量：{score['factors']['strength']}, 乐观：{score['factors']['optimism']})")
            elif questionnaire_id == 'CPSS':
                st.info(f"总分：{score}")
            elif questionnaire_id == 'CSQ':
                st.info(f"类型：{score['style']} (积极：{score['factors']['positive']}, 消极：{score['factors']['negative']})")
            elif questionnaire_id == 'SCL90':
                st.info(f"总分：{score['total']}, 阳性项目：{score['posNum']}")
        
        if st.button("返回主页面"):
            st.session_state.current_questionnaire = None
            st.session_state.show_success_message = False
            st.rerun()
        return
    
    if f'current_responses_{questionnaire_id}' not in st.session_state:
        st.session_state[f'current_responses_{questionnaire_id}'] = {}
    responses = st.session_state[f'current_responses_{questionnaire_id}']
    
    if questionnaire_id == 'CDRISC':
        options = ["从来不", "很少", "有时", "经常", "一直如此"]
        default_val = 2
        opt_range = range(0,5)
        fmt = lambda x: options[x]
    elif questionnaire_id == 'CPSS':
        options = ["从不", "偶尔", "有时", "经常", "总是"]
        default_val = 3
        opt_range = range(1,6)
        fmt = lambda x: options[x-1]
    elif questionnaire_id == 'CSQ':
        options = ["不采取", "偶尔采取", "有时采取", "经常采取"]
        default_val = 1
        opt_range = range(0,4)
        fmt = lambda x: options[x]
    elif questionnaire_id == 'SCL90':
        options = ["没有", "很轻", "中等", "偏重", "严重"]
        default_val = 2
        opt_range = range(1,6)
        fmt = lambda x: options[x-1]
    
    with st.form(key=f"{questionnaire_id}_form"):
        for i, question in enumerate(q_info['questions'], 1):
            current_val = responses.get(i, default_val)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{question}**")
            with col2:
                selected = st.selectbox(
                    label="选择答案",
                    options=opt_range,
                    index=current_val if questionnaire_id in ['CDRISC', 'CSQ'] else current_val-1,
                    format_func=fmt,
                    key=f"{questionnaire_id}_q{i}",
                    label_visibility="collapsed"
                )
                responses[i] = selected
        
        submitted = st.form_submit_button("提交问卷")
    
    if submitted:
        q_count = len(q_info['questions'])
        unanswered = [i for i in range(1, q_count+1) if i not in responses]
        
        if unanswered:
            st.error(f"请完成所有题目！未完成的题目编号：{unanswered}")
        else:
            score = None
            if questionnaire_id == 'CDRISC':
                score = calculate_cdrisc_score(responses)
            elif questionnaire_id == 'CPSS':
                score = calculate_cpss_score(responses)
            elif questionnaire_id == 'CSQ':
                score = calculate_csq_score(responses)
            elif questionnaire_id == 'SCL90':
                score = calculate_scl90_score(responses)
            
            if score:
                st.session_state.questionnaire_responses[questionnaire_id] = responses
                st.session_state.questionnaire_scores[questionnaire_id] = score
                st.session_state.questionnaire_completed[questionnaire_id] = True
                
                if f'current_responses_{questionnaire_id}' in st.session_state:
                    del st.session_state[f'current_responses_{questionnaire_id}']
                
                st.session_state.show_success_message = True
                st.rerun()

def run_comprehensive_assessment():
    scores = st.session_state.questionnaire_scores
    for q_id, completed in st.session_state.questionnaire_completed.items():
        if not completed: 
            st.warning(f"请先完成{QUESTIONNAIRES[q_id]['name']}")
            return

    cdrisc_score = scores['CDRISC']['total'] if scores['CDRISC'] else 0
    cpss_score = scores['CPSS'] if scores['CPSS'] else 0
    csq_style = scores['CSQ']['style'] if scores['CSQ'] else ''
    scl90_total = scores['SCL90']['total'] if scores['SCL90'] else 0

    risk_points = 0
    if cpss_score >= 43: risk_points += 2
    elif cpss_score >= 29: risk_points += 1
    if cdrisc_score <= 50: risk_points += 2
    elif cdrisc_score <= 75: risk_points += 1
    if scl90_total >= 160: risk_points += 2
    if csq_style in ["承受者", "矛盾者"]: risk_points += 1

    if risk_points >= 5: overall_risk = 'red'
    elif risk_points >= 3: overall_risk = 'yellow'
    else: overall_risk = 'green'

    assessment_result = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'scores': {q_id: scores[q_id] for q_id in QUESTIONNAIRES},
        'risk_points': risk_points,
        'overall_risk': overall_risk,
        'recommendations': []
    }

    if overall_risk == 'red':
        assessment_result['recommendations'].append("🔴 **高风险警报**：建议立即寻求专业心理咨询师或医生的帮助。")
        assessment_result['recommendations'].append("🔴 请考虑拨打心理援助热线或前往最近的医疗机构。")
    elif overall_risk == 'yellow':
        assessment_result['recommendations'].append("🟡 **中等风险提示**：建议定期进行心理状态评估，关注自身情绪变化。")
        assessment_result['recommendations'].append("🟡 可以尝试参加心理健康工作坊或学习压力管理技巧。")
    else:
        assessment_result['recommendations'].append("🟢 **低风险状态**：您的心理状态总体良好，请继续保持健康的生活习惯。")

    st.session_state.assessment_result = assessment_result
    
    if save_submission():
        st.success("✅ 评估结果已保存")
    
    return assessment_result

def display_assessment_result(result):
    st.header("综合评估结果")
    st.write(f"评估时间：{result['timestamp']}")
    st.write(f"提交ID：{st.session_state.submission_id}")
    
    if st.session_state.user_info:
        with st.expander("个人信息"):
            info = st.session_state.user_info
            if info.get('name'): st.write(f"**姓名：** {info['name']}")
            if info.get('code'): st.write(f"**编号：** {info['code']}")
            if info.get('note'): st.write(f"**备注：** {info['note']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("各量表情况")
        for q_id in QUESTIONNAIRES:
            score_info = result['scores'].get(q_id)
            if score_info:
                if q_id == 'CDRISC':
                    st.write(f"**{QUESTIONNAIRES[q_id]['name']}**：总分 {score_info['total']}")
                elif q_id == 'CPSS':
                    st.write(f"**{QUESTIONNAIRES[q_id]['name']}**：{score_info} 分")
                elif q_id == 'CSQ':
                    st.write(f"**{QUESTIONNAIRES[q_id]['name']}**：{score_info['style']}")
                elif q_id == 'SCL90':
                    st.write(f"**{QUESTIONNAIRES[q_id]['name']}**：总分 {score_info['total']}")
    with col2:
        st.subheader("综合评估")
        if result['overall_risk'] == 'green': st.success("🟢 总体评估：低风险")
        elif result['overall_risk'] == 'yellow': st.warning("🟡 总体评估：中等风险")
        else: st.error("🔴 总体评估：高风险")
        st.write(f"风险评估点数：{result['risk_points']}")
    st.subheader("个性化建议")
    for rec in result['recommendations']: st.write(rec)

    st.subheader("导出结果")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("生成评估报告"):
            report = f"# 心理健康评估报告\n**时间**：{result['timestamp']}\n**提交ID**：{st.session_state.submission_id}\n\n"
            
            if st.session_state.user_info:
                info = st.session_state.user_info
                if info.get('name'): report += f"**姓名**：{info['name']}\n"
                if info.get('code'): report += f"**编号**：{info['code']}\n"
            
            for q_id in QUESTIONNAIRES:
                score_info = result['scores'].get(q_id)
                if score_info:
                    report += f"- **{QUESTIONNAIRES[q_id]['name']}**："
                    if q_id == 'CDRISC': report += f"总分 {score_info['total']}\n"
                    elif q_id == 'CPSS': report += f"{score_info} 分\n"
                    elif q_id == 'CSQ': report += f"{score_info['style']}\n"
                    elif q_id == 'SCL90': report += f"总分 {score_info['total']}\n"
            report += f"\n**综合风险**：{'低风险 🟢' if result['overall_risk']=='green' else '中等风险 🟡' if result['overall_risk']=='yellow' else '高风险 🔴'}\n"
            st.download_button("下载报告", report, file_name=f"心理评估_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain")
    with col2:
        if st.button("重新评估"):
            for q_id in st.session_state.questionnaire_completed:
                st.session_state.questionnaire_completed[q_id] = False
            st.session_state.assessment_result = None
            st.session_state.submission_id = str(uuid.uuid4())[:8]
            st.rerun()
    with col3:
        if st.button("返回主页"):
            st.session_state.current_questionnaire = None
            st.session_state.assessment_result = None
            st.rerun()

with st.sidebar:
    st.title("🧠 心理健康评估系统")
    completed = sum(st.session_state.questionnaire_completed.values())
    total = len(st.session_state.questionnaire_completed)
    st.info(f"问卷完成进度：{completed}/{total}")
    
    if st.session_state.submission_id:
        st.caption(f"提交ID: {st.session_state.submission_id}")
    
    with st.expander("数据路径"):
        st.caption(f"数据文件: {DATA_FILE}")
        if os.path.exists(DATA_FILE):
            file_size = os.path.getsize(DATA_FILE)
            st.caption(f"文件大小: {file_size/1024:.1f} KB")
        else:
            st.caption("文件不存在")
    
    if st.button("重新初始化系统"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.rerun()
    
    st.markdown("---")
    st.subheader("心理测评量表")
    
    for q_id, q_info in QUESTIONNAIRES.items():
        completed = st.session_state.questionnaire_completed[q_id]
        status = "✅" if completed else "⬜"
        score_disp = f" (已评分)" if completed else ""
        
        if st.button(f"{status} {q_info['name']}{score_disp}", key=f"btn_{q_id}"):
            st.session_state.current_questionnaire = q_id
            st.session_state.show_success_message = False
            st.rerun()
    
    st.markdown("---")
    
    all_done = all(st.session_state.questionnaire_completed.values())
    if st.button("运行综合评估测试", disabled=not all_done, key="btn_assessment"):
        if all_done:
            result = run_comprehensive_assessment()
            if result:
                st.success("评估完成！请返回主页面查看结果。")
                st.rerun()
    
    st.markdown("---")
    if st.button("📊 管理员数据导出"):
        st.session_state.admin_mode = True
        st.session_state.current_questionnaire = None
        st.rerun()

st.title("心理健康评估系统")

if st.session_state.admin_mode:
    show_admin_panel()
elif st.session_state.assessment_result:
    display_assessment_result(st.session_state.assessment_result)
elif st.session_state.current_questionnaire:
    show_questionnaire(st.session_state.current_questionnaire)
else:
    if not st.session_state.user_info.get('name') and not st.session_state.user_info.get('code'):
        show_user_info_form()
        st.markdown("---")
    
    st.markdown("""
    ## 欢迎使用心理健康评估系统
    本系统包含四个标准化心理评估量表：
    1. **心理韧性量表 (CDRISC)** - 评估心理抗压与恢复能力
    2. **压力知觉量表 (CPSS)** - 评估主观压力感知程度
    3. **应急处置应对方式 (CSQ)** - 评估面对困境的应对策略
    4. **症状自评量表 (SCL90)** - 全面评估心理症状严重程度
    
    ### 使用说明：
    1. 在左侧边栏点击要填写的问卷
    2. 根据实际情况回答所有问题
    3. 提交问卷后系统会自动计分
    4. 完成所有问卷后，点击"运行综合评估测试"
    5. 查看综合评估结果和个性化建议
    """)
    
    if st.session_state.user_info:
        with st.expander("📝 我的信息"):
            info = st.session_state.user_info
            if info.get('name'): st.write(f"**姓名：** {info['name']}")
            if info.get('code'): st.write(f"**编号：** {info['code']}")
            if info.get('note'): st.write(f"**备注：** {info['note']}")
            if st.button("修改信息"):
                st.session_state.user_info = {}
                st.rerun()
    
    st.subheader("当前进度")
    cols = st.columns(4)
    for idx, (q_id, q_info) in enumerate(QUESTIONNAIRES.items()):
        with cols[idx]:
            completed = st.session_state.questionnaire_completed[q_id]
            if completed:
                st.success(f"✅ {q_info['name']}")
                score = st.session_state.questionnaire_scores[q_id]
                if score:
                    if q_id == 'CDRISC':
                        st.write(f"总分: {score['total']}")
                    elif q_id == 'CPSS':
                        st.write(f"总分: {score}")
                    elif q_id == 'CSQ':
                        st.write(f"类型: {score['style']}")
                    elif q_id == 'SCL90':
                        st.write(f"总分: {score['total']}")
            else:
                st.info(f"⬜ {q_info['name']}")
                st.write("待完成")
