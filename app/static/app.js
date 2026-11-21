const $ = (s) => document.querySelector(s);
const sideMenu = $("#sideMenu"), scrim = $("#scrim"), modal = $("#authModal");
function openMenu(){sideMenu.classList.add("open");scrim.classList.add("open")}
function closeMenu(){sideMenu.classList.remove("open");scrim.classList.remove("open")}
$("#menuToggle").addEventListener("click",openMenu);
$("#menuClose").addEventListener("click",closeMenu);
scrim.addEventListener("click",closeMenu);
sideMenu.querySelectorAll("a").forEach(a=>a.addEventListener("click",closeMenu));
$("#year").textContent = new Date().getFullYear();

let authMode="login";
function openAuth(mode="login"){setAuthMode(mode);modal.classList.add("open");modal.setAttribute("aria-hidden","false")}
function closeAuth(){modal.classList.remove("open");modal.setAttribute("aria-hidden","true")}
function setAuthMode(mode){authMode=mode;document.querySelectorAll(".auth-tabs button").forEach(b=>b.classList.toggle("selected",b.dataset.mode===mode));$("#nameField").classList.toggle("hidden",mode!=="register");$("#authTitle").textContent=mode==="login"?"Xush kelibsiz!":"Yangi hisob yarating";$("#authDescription").textContent=mode==="login"?"Hisobingizga kiring va o‘rganishni davom ettiring.":"VIZOR’da o‘rganishni boshlash uchun ro‘yxatdan o‘ting." ;$("#authSubmit").textContent=mode==="login"?"Kirish":"Hisob yaratish";$("#formMessage").textContent=""}
$("#loginOpen").addEventListener("click",()=>openAuth("login"));
$("#mobileLogin").addEventListener("click",()=>openAuth("login"));
$("#registerOpen").addEventListener("click",()=>openAuth("register"));
$("#sideRegister").addEventListener("click",()=>{closeMenu();openAuth("register")});
$("#ctaRegister").addEventListener("click",()=>openAuth("register"));
$("#authClose").addEventListener("click",closeAuth);
modal.addEventListener("click",e=>{if(e.target===modal)closeAuth()});
document.querySelectorAll(".auth-tabs button").forEach(b=>b.addEventListener("click",()=>setAuthMode(b.dataset.mode)));
$("#authForm").addEventListener("submit",async e=>{
  e.preventDefault();const form=new FormData(e.currentTarget);const payload={email:form.get("email"),password:form.get("password")};
  if(authMode==="register"){payload.full_name=form.get("full_name");payload.role="student"}
  const button=$("#authSubmit");button.disabled=true;button.textContent="Tekshirilmoqda…";$("#formMessage").textContent="";
  try{const response=await fetch(authMode==="login"?"/api/auth/login":"/api/auth/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const data=await response.json();if(!response.ok)throw new Error(data.detail||"So‘rov bajarilmadi");sessionStorage.setItem("vizor_token",data.access_token);$("#formMessage").textContent="Muvaffaqiyatli!";button.textContent="Tayyor";setTimeout(closeAuth,800)}catch(err){$("#formMessage").textContent=err.message;button.disabled=false;button.textContent=authMode==="login"?"Kirish":"Hisob yaratish"}
});
const sampleCourses=[
 {title:"Dasturlash asoslari",description:"Dasturlash mantig‘i va ilk kodlaringiz bilan tanishing.",category:"Dasturlash",level:"Boshlang‘ich",symbol:"</>"},
 {title:"Grafik dizayn asoslari",description:"Rang, kompozitsiya va vizual fikrlashni o‘rganing.",category:"Dizayn",level:"Boshlang‘ich",symbol:"✎"},
 {title:"Ingliz tili",description:"Kundalik muloqot uchun kerakli bilimlarni mustahkamlang.",category:"Tillar",level:"Boshlang‘ich",symbol:"文"},
 {title:"Raqamli marketing",description:"Internetda mahsulot va xizmatlarni targ‘ib qilish asoslari.",category:"Biznes",level:"Amaliy",symbol:"↗"},
 {title:"Mobil videografiya",description:"Telefon orqali sifatli video olish va montaj qilish.",category:"Media",level:"Amaliy",symbol:"▣"},
 {title:"Shaxsiy rivojlanish",description:"Maqsad qo‘yish, vaqtni boshqarish va samarali odatlar.",category:"Shaxsiy rivojlanish",level:"Barcha uchun",symbol:"✦"}
];
let courses=[];
function renderCourses(){
 const q=$("#courseSearch").value.trim().toLocaleLowerCase("uz");const category=$("#categoryFilter").value;
 const filtered=courses.filter(c=>(!category||c.category.toLocaleLowerCase("uz").includes(category.toLocaleLowerCase("uz")))&&(!q||(c.title+" "+c.description+" "+c.category).toLocaleLowerCase("uz").includes(q)));
 $("#courseCount").textContent=filtered.length+" ta kurs";
 $("#courseGrid").innerHTML=filtered.length?filtered.map((c,i)=>`<article class="course-card"><div class="course-cover" style="background:${["linear-gradient(135deg,#173a70,#087f8c)","linear-gradient(135deg,#4c4387,#8a78bd)","linear-gradient(135deg,#8b6523,#d7a94d)","linear-gradient(135deg,#165b67,#36a39a)"][i%4]}"><span class="cover-symbol">${escapeHtml(c.symbol||"▤")}</span><span class="course-level">${escapeHtml(c.level||"Ochiq kurs")}</span></div><div class="course-info"><span class="course-category">${escapeHtml(c.category||"Umumiy")}</span><h3>${escapeHtml(c.title)}</h3><p>${escapeHtml(c.description||"Kurs haqida batafsil ma’lumot.")}</p><div class="course-meta"><span>VIZOR ta’lim</span><button class="course-link" data-course="${escapeHtml(String(c.id||""))}">Kursni ko‘rish →</button></div></div></article>`).join(""):`<div class="empty-card">Bu qidiruv bo‘yicha kurs topilmadi. Boshqa so‘z bilan qidiring.</div>`;
}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]))}
async function loadCourses(){
 try{const response=await fetch("/api/public/courses");if(!response.ok)throw new Error("API unavailable");const data=await response.json();courses=Array.isArray(data)&&data.length?data.map(c=>({...c,level:"Ochiq kurs",symbol:"▤"})):sampleCourses;renderCourses()}
 catch{courses=sampleCourses;renderCourses()}
}
$("#courseSearch").addEventListener("input",renderCourses);
$("#categoryFilter").addEventListener("change",renderCourses);
document.querySelectorAll(".category-card").forEach(card=>card.addEventListener("click",()=>{const category=card.dataset.category;$("#categoryFilter").value=[...$("#categoryFilter").options].some(o=>o.value===category)?category:"";renderCourses()}));
$("#courseGrid").addEventListener("click",e=>{if(e.target.matches("[data-course]"))openAuth("login")});
loadCourses();