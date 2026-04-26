"""
Generate a co-parenting custody portal HTML from calendar JSON.

Reads:
- calendar_data.json (school breaks, noschool days)
- district name, state

Generates:
- index.html -- SPO and ESPO custody calendar

The output is a standalone HTML file with:
- SPO Calendar (Standard Possession Order: every Thursday Dad 6-8pm, 1st/3rd/5th Fri-Sat-Sun)
- ESPO Calendar (Expanded: alternating schedule, holidays, spring/christmas breaks)
- Language toggle: English / 中文
"""
import json
import sys
from datetime import datetime, timedelta

DEFAULT_SCHOOL_DATA = {
    "district": "Round Rock ISD",
    "state": "Texas",
    "schoolYears": {
        "2025-2026": {
            "yearLabel": "2025-2026",
            "firstDay": "2025-08-12",
            "lastDay": "2026-05-21",
            "schoolResumes": "2026-08-13",
            "breaks": {
                "thanksgiving": {"start": "2025-11-24", "end": "2025-11-28", "schoolResumes": "2025-12-01"},
                "christmas": {"lastInstructionDay": "2025-12-19", "breakStart": "2025-12-20", "schoolResumes": "2026-01-06", "custodyEnd": "2026-01-05"},
                "spring": {"start": "2026-03-16", "end": "2026-03-20", "schoolResumes": "2026-03-23"}
            },
            "noschool": [
                {"date": "2025-09-01", "label": "Labor Day"},
                {"date": "2025-09-22", "label": "Student Holiday (Rosh Hashanah)"},
                {"date": "2025-09-23", "label": "Student Holiday (Rosh Hashanah)"},
                {"date": "2025-10-13", "label": "Student Holiday (Indigenous Peoples' Day)"},
                {"date": "2025-10-20", "label": "Student Holiday (Diwali)"},
                {"date": "2025-11-07", "label": "Staff Development Day"},
                {"date": "2026-01-19", "label": "MLK Jr. Day"},
                {"date": "2026-02-16", "label": "Presidents Day"},
                {"date": "2026-02-17", "label": "Student Holiday (Lunar New Year)"},
                {"date": "2026-04-03", "label": "Good Friday"},
                {"date": "2026-05-25", "label": "Memorial Day"},
            ]
        }
    }
}

def date_range(start_str, end_str):
    """Generate all dates from start to end (inclusive)."""
    start = datetime.strptime(start_str, '%Y-%m-%d')
    end = datetime.strptime(end_str, '%Y-%m-%d')
    dates = []
    while start <= end:
        dates.append(start.strftime('%Y-%m-%d'))
        start += timedelta(days=1)
    return dates

def build_school_breaks(cal_data):
    """Build flat schoolBreaks array from calendar JSON."""
    breaks = []
    for year_label, sy in cal_data.get('schoolYears', {}).items():
        yr = year_label[:4]
        # Thanksgiving
        tg = sy.get('breaks', {}).get('thanksgiving', {})
        if tg:
            breaks.append({
                'start': tg['start'], 'end': tg['end'],
                'label': {'en': 'Fall Break', 'cn': '秋假'}
            })
        # Christmas/Winter
        xm = sy.get('breaks', {}).get('christmas', {})
        if xm:
            custody_end = xm.get('custodyEnd', xm.get('schoolResumes', '')[:-3] + '04')
            breaks.append({
                'start': xm.get('lastInstructionDay', xm.get('breakStart', '')),
                'end': custody_end,
                'schoolResumes': xm.get('schoolResumes', ''),
                'label': {'en': 'Winter Break', 'cn': '寒假'}
            })
        # Spring
        sp = sy.get('breaks', {}).get('spring', {})
        if sp:
            breaks.append({
                'start': sp['start'], 'end': sp['end'],
                'label': {'en': 'Spring Break', 'cn': '春假'}
            })
        # Summer: day after lastDay to day before schoolResumes
        last_day = sy.get('lastDay', '')
        school_resumes = sy.get('schoolResumes', '')
        if last_day and school_resumes:
            summer_start = (datetime.strptime(last_day, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            summer_end = (datetime.strptime(school_resumes, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            breaks.append({
                'start': summer_start, 'end': summer_end,
                'schoolResumes': school_resumes,
                'label': {'en': 'Summer Break', 'cn': '暑假'}
            })
    return breaks

def generate_html(cal_data):
    school_breaks = build_school_breaks(cal_data)
    school_breaks_json = json.dumps(school_breaks, ensure_ascii=False)

    # Build noschool Set
    noschool_list = []
    for year_label, sy in cal_data.get('schoolYears', {}).items():
        for ns in sy.get('noschool', []):
            noschool_list.append({'date': ns['date'], 'label': ns.get('label', ns.get('label_en', 'No School'))})
    noschool_json = json.dumps(noschool_list, ensure_ascii=False)

    district = cal_data.get('district', 'School District')
    state = cal_data.get('state', 'TX')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{district} Co-Parenting Portal | 共同抚养门户</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #fff; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .lang-toggle {{ display: flex; justify-content: flex-end; gap: 10px; padding: 20px; }}
        .lang-btn {{ padding: 8px 20px; border: 2px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); color: #fff; border-radius: 20px; cursor: pointer; }}
        .lang-btn.active {{ background: rgba(255,255,255,0.2); }}
        h1 {{ text-align: center; margin: 20px 0; font-size: 2em; }}
        .calendar-row {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; margin-bottom: 40px; }}
        .month-calendar {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 15px; min-width: 280px; flex: 1; }}
        .month-calendar h3 {{ text-align: center; margin-bottom: 10px; color: #aaa; }}
        .cal-weekdays {{ display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-size: 0.8em; color: #888; margin-bottom: 5px; }}
        .cal-days {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }}
        .cal-day {{ aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 6px; font-size: 0.9em; position: relative; }}
        .cal-day.dad {{ background: rgba(220, 53, 69, 0.3); border: 1px solid rgba(220, 53, 69, 0.5); }}
        .cal-day.mom {{ background: rgba(111, 66, 193, 0.3); border: 1px solid rgba(111, 66, 193, 0.5); }}
        .cal-day.other-month {{ opacity: 0.3; }}
        .day-num {{ font-weight: bold; }}
        .day-label {{ font-size: 0.6em; color: #ccc; text-align: center; overflow: hidden; }}
        .legend {{ display: flex; justify-content: center; gap: 30px; margin: 20px 0; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; }}
        .legend-dot {{ width: 20px; height: 20px; border-radius: 4px; }}
        .legend-dot.dad {{ background: rgba(220, 53, 69, 0.5); }}
        .legend-dot.mom {{ background: rgba(111, 66, 193, 0.5); }}
        .section-tabs {{ display: flex; justify-content: center; gap: 10px; margin: 20px 0; }}
        .tab-btn {{ padding: 10px 30px; border: none; border-radius: 20px; cursor: pointer; font-size: 1em; background: rgba(255,255,255,0.1); color: #fff; }}
        .tab-btn.active {{ background: rgba(255,255,255,0.3); }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .uncertain-break {{ border: 1px dashed #666 !important; opacity: 0.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="lang-toggle">
            <button class="lang-btn active" onclick="setLang('en')">EN</button>
            <button class="lang-btn" onclick="setLang('cn')">中文</button>
        </div>
        <h1>{district} -- Co-Parenting Calendar</h1>
        <div class="legend">
            <div class="legend-item"><div class="legend-dot dad"></div><span>Dad</span></div>
            <div class="legend-item"><div class="legend-dot mom"></div><span>Mom</span></div>
        </div>
        <div class="section-tabs">
            <button class="tab-btn active" onclick="showSection('spo')">SPO Calendar</button>
            <button class="tab-btn" onclick="showSection('espo')">ESPO Calendar</button>
        </div>
        <div id="spoContainer" class="tab-content active"></div>
        <div id="espoContainer" class="tab-content"></div>
    </div>
    <script>
    const schoolBreaks = {school_breaks_json};
    const noschoolDays = {noschool_json};
    const noSchoolSet = new Set(noschoolDays.map(n => n.date));
    const nationalHolidays = [
        {{ month: 0, day: 1, label: {{ en: "New Year's Day", cn: '元旦' }} }},
        {{ month: 0, monday: 2, label: {{ en: 'MLK Day', cn: '马丁路德金日' }} }},
        {{ month: 1, day: 14, label: {{ en: 'Valentine\\'s Day', cn: '情人节' }} }},
        {{ month: 2, day: 17, label: {{ en: 'St. Patrick\\'s Day', cn: '圣帕特里克节' }} }},
        {{ month: 3, day: 4, label: {{ en: 'Easter Sunday', cn: '复活节' }} }},
        {{ month: 4, day: 1, label: {{ en: 'Cinco de Mayo', cn: '五日节' }} }},
        {{ month: 5, monday: 3, label: {{ en: 'Memorial Day', cn: '阵亡将士纪念日' }} }},
        {{ month: 6, day: 4, label: {{ en: 'Independence Day', cn: '美国独立日' }} }},
        {{ month: 8, monday: 1, label: {{ en: 'Labor Day', cn: '劳动节' }} }},
        {{ month: 9, day: 12, label: {{ en: 'Columbus Day', cn: '哥伦布日' }} }},
        {{ month: 9, day: 31, label: {{ en: 'Halloween', cn: '万圣节' }} }},
        {{ month: 10, day: 11, label: {{ en: 'Veterans Day', cn: '退伍军人节' }} }},
        {{ month: 10, day: 27, label: {{ en: 'Thanksgiving', cn: '感恩节' }} }},
        {{ month: 10, friday: 4, label: {{ en: 'Day after Thanksgiving', cn: '黑色星期五' }} }},
        {{ month: 11, day: 25, label: {{ en: 'Christmas Day', cn: '圣诞节' }} }},
    ];

    const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    const MONTHS_CN = ['一月','二月','三月','四月','五月','六月','七月','八月','九月','十月','十一月','十二月'];
    const WEEKDAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    const WEEKDAYS_CN = ['周日','周一','周二','周三','周四','周五','周六'];

    let lang = 'en';
    function setLang(l) {{ lang = l; document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.textContent === (l === 'en' ? 'EN' : '中文'))); generateESPOCalendar(lang); generateSPOCalendar(lang); }}
    function showSection(s) {{ document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.textContent.toLowerCase().includes(s))); document.getElementById('spoContainer').classList.toggle('active', s === 'spo'); document.getElementById('espoContainer').classList.toggle('active', s === 'espo'); }}

    function isSchoolYearEven(yr) {{ return yr % 2 === 0; }}
    function getSchoolYear(dateStr) {{ const [y,m] = dateStr.split('-').map(Number); return m >= 8 ? y : y - 1; }}

    function isSchoolBreak(dateStr) {{
        const d = new Date(dateStr);
        for (const br of schoolBreaks) {{
            if (d >= new Date(br.start) && d <= new Date(br.end)) return br;
        }}
        return null;
    }}

    function isNoSchoolDay(dateStr) {{ return noSchoolSet.has(dateStr); }}

    function getChristmasCustody(dateStr) {{
        const [y,m,d] = dateStr.split('-').map(Number);
        const sy = m >= 8 ? y : y - 1;
        const evenSY = isSchoolYearEven(sy);
        const xYear = m <= 4 ? sy : y;
        for (const br of schoolBreaks) {{
            if (br.label.en !== 'Winter Break' && br.label.cn !== '寒假') continue;
            const [bsy,bsm] = br.start.split('-').map(Number);
            if (bsm !== 12 || bsy !== xYear) continue;
            const [xey,xem,xed] = br.end.split('-').map(Number);
            const xStart = new Date(bsy,bsm-1,bsm===12?br.start.split('-')[2]:1);
            const xEnd = new Date(xey,xem-1,xed);
            if (d >= xStart && d <= xEnd) {{
                if (m === 12 && d === 28) return evenSY ? 'dad' : 'mom';
                if (m === 12 && d < 28) return evenSY ? 'dad' : 'mom';
                return evenSY ? 'mom' : 'dad';
            }}
        }}
        return 'none';
    }}

    function getThanksgivingCustody(dateStr) {{
        const [y,m,d] = dateStr.split('-').map(Number);
        const sy = m >= 8 ? y : y - 1;
        const evenSY = isSchoolYearEven(sy);
        for (const br of schoolBreaks) {{
            if (br.label.en !== 'Fall Break' && br.label.cn !== '秋假') continue;
            const [sy2,sm2,sd2] = br.start.split('-').map(Number);
            const [ey2,em2,ed2] = br.end.split('-').map(Number);
            const start = new Date(sy2,sm2-1,sd2);
            const end = new Date(ey2,em2-1,ed2);
            const dd = new Date(y,m-1,d);
            if (dd >= start && dd <= end) {{
                const dow = dd.getDay();
                // First half: Mon, Tue, Wed (dow 1,2,3) -> first parent
                // Second half: Thu, Fri (dow 4,5) -> second parent
                const mid = new Date(start); mid.setDate(mid.getDate() + Math.floor((end - start) / 86400000 / 2));
                return dd <= mid ? (evenSY ? 'mom' : 'dad') : (evenSY ? 'dad' : 'mom');
            }}
        }}
        return 'none';
    }}

    function getSchoolBreakCustody(dateStr) {{
        const [y,m,d] = dateStr.split('-').map(Number);
        const sy = m >= 8 ? y : y - 1;
        const evenSY = isSchoolYearEven(sy);
        const xYear = m <= 4 ? sy : y;
        for (const br of schoolBreaks) {{
            if (br.label.en === 'Fall Break' || br.label.cn === '秋假') {{
                const [sy2,sm2,sd2] = br.start.split('-').map(Number);
                const [ey2,em2,ed2] = br.end.split('-').map(Number);
                const start = new Date(sy2,sm2-1,sd2);
                const end = new Date(ey2,em2-1,ed2);
                const dd = new Date(y,m-1,d);
                if (dd >= start && dd <= end) {{
                    const mid = new Date(start); mid.setDate(mid.getDate() + Math.floor((end - start) / 86400000 / 2));
                    return dd <= mid ? (evenSY ? 'mom' : 'dad') : (evenSY ? 'dad' : 'mom');
                }}
            }}
            if (br.label.en === 'Winter Break' || br.label.cn === '寒假') {{
                const [bsy,bsm] = br.start.split('-').map(Number);
                if (bsm !== 12 || bsy !== xYear) continue;
                const [bsd] = br.start.split('-').map(Number);
                const [xey,xem,xed] = br.end.split('-').map(Number);
                const xStart = new Date(bsy,bsm-1,bsd);
                const xEnd = new Date(xey,xem-1,xed);
                const dd = new Date(y,m-1,d);
                if (dd >= xStart && dd <= xEnd) {{
                    if (m === 12 && d === 28) return evenSY ? 'dad' : 'mom';
                    if (m === 12 && d < 28) return evenSY ? 'dad' : 'mom';
                    return evenSY ? 'mom' : 'dad';
                }}
            }}
            if (br.label.en === 'Spring Break' || br.label.cn === '春假') {{
                const [sby,sbm,sbd] = br.start.split('-').map(Number);
                const [eby,ebm,ebd] = br.end.split('-').map(Number);
                const sStart = new Date(sby,sbm-1,sbd);
                const sEnd = new Date(eby,ebm-1,ebd);
                const dd = new Date(y,m-1,d);
                if (dd >= sStart && dd <= sEnd) return evenSY ? 'mom' : 'dad';
            }}
        }}
        return 'none';
    }}

    function getNationalHolidayLabel(year, month, day) {{
        for (const h of nationalHolidays) {{
            if (h.month !== month || (h.year && h.year !== year)) continue;
            if (h.day && h.day === day) return h.label;
            if (h.monday) {{ const d = new Date(year,month,1); let count=0; for(let i=0;i<31;i++){{ const dd=new Date(year,month,i+1); if(dd.getDay()===1){{count++;if(count===h.monday&&dd.getDate()===day)return h.label;}}}} }}
            if (h.friday) {{ const d = new Date(year,month,1); let count=0; for(let i=0;i<31;i++){{ const dd=new Date(year,month,i+1); if(dd.getDay()===5){{count++;if(count===h.friday&&dd.getDate()===day)return h.label;}}}} }}
        }}
        return null;
    }}

    function generateSPOCalendar() {{
        const container = document.getElementById('spoContainer');
        container.innerHTML = '';
        const y0 = new Date().getFullYear();
        const years = [y0, y0+1];
        let html = '';
        for (const yr of years) {{
            for (let mo=0; mo<12; mo++) {{
                const firstDay = new Date(yr, mo, 1);
                const lastDate = new Date(yr, mo+1, 0).getDate();
                const startPad = firstDay.getDay();
                const mname = lang === 'en' ? MONTHS[mo] : MONTHS_CN[mo];
                html += `<div class="month-calendar"><h3>${{mname}} ${{yr}}</h3>`;
                const wds = lang === 'en' ? WEEKDAYS : WEEKDAYS_CN;
                html += `<div class="cal-weekdays">${{wds.map(w=>`<div>${{w}}</div>`).join('')}}</div>`;
                html += `<div class="cal-days">`;
                for (let i=0;i<startPad;i++) html+=`<div class="cal-day other-month"><div class="day-num"></div></div>`;
                for (let d=1; d<=lastDate; d++) {{
                    const dateStr = `${{yr}}-${{String(mo+1).padStart(2,'0')}}-${{String(d).padStart(2,'0')}}`;
                    const dow = new Date(yr, mo, d).getDay();
                    const breakInfo = isSchoolBreak(dateStr);
                    const isThursday = dow === 4;
                    const isFriday = dow === 5;
                    const isSaturday = dow === 6;
                    const isSunday = dow === 0;
                    let cls = 'dad', label = lang==='cn'?'爸爸6-8pm':'Dad 6-8pm';
                    if (isThursday) {{ cls='dad'; label=lang==='cn'?'爸爸6-8pm':'Dad 6-8pm'; }}
                    else if (isFriday || isSaturday || isSunday) {{ cls='mom'; label=''; }}
                    else {{ cls='mom'; label=''; }}
                    html += `<div class="cal-day ${{cls}}"><div class="day-num">${{d}}</div><div class="day-label">${{label}}</div></div>`;
                }}
                html += `</div></div>`;
            }}
        }}
        container.innerHTML = html;
    }}

    function generateESPOCalendar() {{
        const container = document.getElementById('espoContainer');
        container.innerHTML = '';
        const y0 = new Date().getFullYear();
        const years = [y0, y0+1];
        let html = '';
        for (const yr of years) {{
            for (let mo=0; mo<12; mo++) {{
                const firstDay = new Date(yr, mo, 1);
                const lastDate = new Date(yr, mo+1, 0).getDate();
                const startPad = firstDay.getDay();
                const mname = lang === 'en' ? MONTHS[mo] : MONTHS_CN[mo];
                html += `<div class="month-calendar"><h3>${{mname}} ${{yr}}</h3>`;
                const wds = lang === 'en' ? WEEKDAYS : WEEKDAYS_CN;
                html += `<div class="cal-weekdays">${{wds.map(w=>`<div>${{w}}</div>`).join('')}}</div>`;
                html += `<div class="cal-days">`;
                for (let i=0;i<startPad;i++) html+=`<div class="cal-day other-month"><div class="day-num"></div></div>`;
                for (let d=1; d<=lastDate; d++) {{
                    const dateStr = `${{yr}}-${{String(mo+1).padStart(2,'0')}}-${{String(d).padStart(2,'0')}}`;
                    const dow = new Date(yr, mo, d).getDay();
                    const breakInfo = isSchoolBreak(dateStr);
                    const natHoliday = getNationalHolidayLabel(yr, mo, d);
                    let cls='mom', label='';
                    if (breakInfo) {{
                        const bc = getSchoolBreakCustody(dateStr);
                        cls = bc; label = breakInfo.label[lang] || breakInfo.label.en;
                    }} else if (natHoliday) {{
                        cls = yr % 2 === 1 ? 'dad' : 'mom';
                        label = natHoliday[lang] || natHoliday.en;
                    }} else if (isNoSchoolDay(dateStr)) {{
                        cls = yr % 2 === 1 ? 'dad' : 'mom';
                        label = 'No School';
                    }}
                    html += `<div class="cal-day ${{cls}}"><div class="day-num">${{d}}</div><div class="day-label">${{label}}</div></div>`;
                }}
                html += `</div></div>`;
            }}
        }}
        container.innerHTML = html;
    }}

    generateSPOCalendar();
    generateESPOCalendar();
    </script>
</body>
</html>'''
    return html

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'calendar_data.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'index.html'

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            cal_data = json.load(f)
    except FileNotFoundError:
        print(f"Using default sample data: {input_file} not found")
        cal_data = DEFAULT_SCHOOL_DATA

    html = generate_html(cal_data)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated: {output_file}")
