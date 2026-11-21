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
 $("#courseGrid").innerHTML=filtered.length?filtered.map((c,i)=>{const price=c.is_free===false?new Intl.NumberFormat("uz-UZ").format(c.price_minor||0)+" "+(c.currency||"UZS"):"Bepul";return `<article class="course-card"><div class="course-cover" style="background:${["linear-gradient(135deg,#173a70,#087f8c)","linear-gradient(135deg,#4c4387,#8a78bd)","linear-gradient(135deg,#8b6523,#d7a94d)","linear-gradient(135deg,#165b67,#36a39a)"][i%4]}"><span class="cover-symbol">${escapeHtml(c.symbol||"▤")}</span><span class="course-level">${escapeHtml(c.level||"Ochiq kurs")}</span></div><div class="course-info"><span class="course-category">${escapeHtml(c.category||"Umumiy")}</span><h3>${escapeHtml(c.title)}</h3><p>${escapeHtml(c.description||"Kurs haqida batafsil ma’lumot.")}</p><div class="course-meta"><span class="course-price ${c.is_free===false?"paid":""}">${escapeHtml(price)}</span><button class="course-link" data-course="${escapeHtml(String(c.id||""))}">Kursni ko‘rish →</button></div></div></article>`}).join(""):`<div class="empty-card">Bu qidiruv bo‘yicha kurs topilmadi. Boshqa so‘z bilan qidiring.</div>`;
}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]))}
async function loadCourses(){
 try{const response=await fetch("/api/education/catalog");if(!response.ok)throw new Error("API unavailable");const data=await response.json();courses=Array.isArray(data)?data.map(c=>({...c,level:"Ochiq kurs",symbol:"▤"})):[];renderCourses()}
 catch{courses=sampleCourses.map(c=>({...c,is_free:true}));renderCourses()}
}
$("#courseSearch").addEventListener("input",renderCourses);
$("#categoryFilter").addEventListener("change",renderCourses);
document.querySelectorAll(".category-card").forEach(card=>card.addEventListener("click",()=>{const category=card.dataset.category;$("#categoryFilter").value=[...$("#categoryFilter").options].some(o=>o.value===category)?category:"";renderCourses()}));
let selectedCourse=null;
const courseModal=$("#courseModal");
function closeCourse(){courseModal.classList.remove("open");courseModal.setAttribute("aria-hidden","true")}
$("#courseClose").addEventListener("click",closeCourse);
courseModal.addEventListener("click",e=>{if(e.target===courseModal)closeCourse()});
function safeLink(value){try{const u=new URL(value,location.origin);return ["http:","https:"].includes(u.protocol)?u.href:""}catch{return ""}}
function youtubeEmbedUrl(raw){
 try{const u=new URL(raw);let id="";
 if(["youtu.be"].includes(u.hostname))id=u.pathname.split("/").filter(Boolean)[0]||"";
 else if(["youtube.com","www.youtube.com","m.youtube.com","youtube-nocookie.com","www.youtube-nocookie.com"].includes(u.hostname)){if(u.pathname==="/watch")id=u.searchParams.get("v")||"";else if(u.pathname.startsWith("/embed/")||u.pathname.startsWith("/shorts/"))id=u.pathname.split("/")[2]||""}
 return /^[A-Za-z0-9_-]{11}$/.test(id)?"https://www.youtube-nocookie.com/embed/"+id+"?playsinline=1&rel=0":""}catch{return ""}
}
function showMaterials(data){
 const blocks=[];
 (data.lessons||[]).forEach((lesson,i)=>{let assets=(lesson.assets||[]).map(asset=>{if(asset.kind==="text")return `<p>${escapeHtml(asset.body||"")}</p>`;if(asset.kind==="video"){const embed=youtubeEmbedUrl(asset.url||"");return embed?`<div class="vizor-video-frame"><iframe src="${embed}" title="${escapeHtml(asset.title)}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>`:""}const href=safeLink(asset.url);return href?`<a href="${escapeHtml(href)}" target="_blank" rel="noopener">${escapeHtml(asset.kind.toUpperCase()+" · "+asset.title)}</a>`:""}).join("");const embed=youtubeEmbedUrl(lesson.video_url||"");const video=embed?`<div class="vizor-video-frame"><iframe src="${embed}" title="${escapeHtml(lesson.title)}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>`:"";blocks.push(`<article class="lesson-detail"><h3>${i+1}. ${escapeHtml(lesson.title)}</h3><p>${escapeHtml(lesson.content||"")}</p>${video}${assets}</article>`)});
 (data.practicals||[]).forEach(task=>blocks.push(`<article class="practical-detail"><strong>Amaliyot: ${escapeHtml(task.title)}</strong><p>${escapeHtml(task.instructions)}</p></article>`));
 $("#courseDetailBody").innerHTML=blocks.length?blocks.join(""):"<p>Bu kursga hali darslar joylanmagan.</p>";
}
async function loadCourseMaterials(){
 if(!selectedCourse||!selectedCourse.id)return;
 $("#courseDetailBody").innerHTML="<p>Darslar yuklanmoqda…</p>";
 try{const token=sessionStorage.getItem("vizor_token");const response=await fetch("/api/education/courses/"+selectedCourse.id+"/materials",{headers:token?{Authorization:"Bearer "+token}:{}});const data=await response.json();if(!response.ok)throw new Error(data.detail||"Darslarni yuklab bo‘lmadi");showMaterials(data);$("#courseAccessButton").classList.add("hidden");$("#courseDetailMessage").textContent=""}
 catch(err){$("#courseDetailBody").innerHTML=`<p>${escapeHtml(err.message)}</p>`}
}
async function openCourse(id){
 selectedCourse=courses.find(c=>String(c.id)===String(id));
 if(!selectedCourse)return;
 $("#courseDetailCategory").textContent=selectedCourse.category||"VIZOR KURSI";
 $("#courseDetailTitle").textContent=selectedCourse.title;
 $("#courseDetailDescription").textContent=selectedCourse.description||"Kurs darslari va materiallari.";
 $("#courseDetailBody").innerHTML="";
 $("#courseDetailMessage").textContent="";
 $("#courseAccessButton").classList.remove("hidden");
 $("#courseAccessButton").textContent=selectedCourse.is_free===false?"Pullik kursga ruxsat so‘rash":"Darslarni ochish";
 courseModal.classList.add("open");courseModal.setAttribute("aria-hidden","false");
 if(selectedCourse.is_free!==false)await loadCourseMaterials();
 else $("#courseDetailBody").innerHTML="<p>Bu pullik kurs. Kurs materiallarini ochish uchun hisobingizga kiring va to‘lov tasdiqlangach ruxsat oling.</p>";
}
$("#courseAccessButton").addEventListener("click",async()=>{
 if(!selectedCourse)return;
 if(selectedCourse.is_free!==false){await loadCourseMaterials();return}
 const token=sessionStorage.getItem("vizor_token");
 if(!token){closeCourse();openAuth("login");return}
 const button=$("#courseAccessButton");button.disabled=true;button.textContent="So‘rov yuborilmoqda…";
 try{const response=await fetch("/api/education/courses/"+selectedCourse.id+"/access-request",{method:"POST",headers:{Authorization:"Bearer "+token}});const data=await response.json();if(!response.ok)throw new Error(data.detail||"So‘rov yuborilmadi");if(data.status==="approved"){await loadCourseMaterials()}else{$("#courseDetailMessage").textContent="So‘rovingiz yuborildi. To‘lov tekshirilgach kurs ochiladi.";button.textContent="So‘rov yuborildi"}}
 catch(err){$("#courseDetailMessage").textContent=err.message;button.disabled=false;button.textContent="Qayta urinish"}
});
$("#courseGrid").addEventListener("click",e=>{const button=e.target.closest("[data-course]");if(button)openCourse(button.dataset.course)});

const teacherPublishModal=$("#teacherPublishModal");
function closeTeacherPublish(){teacherPublishModal.classList.remove("open");teacherPublishModal.setAttribute("aria-hidden","true")}
$("#teacherPublishOpen").addEventListener("click",()=>{if(!sessionStorage.getItem("vizor_token")){openAuth("login");return}teacherPublishModal.classList.add("open");teacherPublishModal.setAttribute("aria-hidden","false")});
$("#teacherPublishClose").addEventListener("click",closeTeacherPublish);
teacherPublishModal.addEventListener("click",e=>{if(e.target===teacherPublishModal)closeTeacherPublish()});
$("#publishOffer").addEventListener("change",e=>$("#publishPriceWrap").classList.toggle("hidden",e.target.value!=="paid"));
$("#teacherPublishForm").addEventListener("submit",async e=>{
 e.preventDefault();const form=new FormData(e.currentTarget);const token=sessionStorage.getItem("vizor_token");if(!token){openAuth("login");return}
 const youtube= youtubeEmbedUrl(form.get("youtube_url"));if(!youtube){$("#teacherPublishMessage").textContent="YouTube havolasi noto‘g‘ri. To‘g‘ri video havolasini kiriting.";return}
 const paid=form.get("offer")==="paid";const price=Number(form.get("price")||0);if(paid&&(!Number.isSafeInteger(price)||price<1)){$("#teacherPublishMessage").textContent="Pullik kurs uchun narxni to‘g‘ri kiriting.";return}
 const button=$("#teacherPublishSubmit");button.disabled=true;button.textContent="Joylanmoqda…";$("#teacherPublishMessage").textContent="";
 const headers={"Content-Type":"application/json",Authorization:"Bearer "+token};
 try{
  let response=await fetch("/api/courses",{method:"POST",headers,body:JSON.stringify({title:form.get("title"),description:form.get("description"),category:form.get("category")})});let course=await response.json();if(!response.ok)throw new Error(course.detail||"Kurs yaratilmadi");
  response=await fetch("/api/education/courses/"+course.id+"/offer",{method:"PUT",headers,body:JSON.stringify({is_free:!paid,price_minor:paid?price:0,currency:"UZS"})});let offer=await response.json();if(!response.ok)throw new Error(offer.detail||"Kurs narxi saqlanmadi");
  response=await fetch("/api/courses/"+course.id+"/lessons",{method:"POST",headers,body:JSON.stringify({title:form.get("lesson_title"),content:form.get("lesson_content"),video_url:form.get("youtube_url"),position:1})});let lesson=await response.json();if(!response.ok)throw new Error(lesson.detail||"Dars yaratilmadi");
  response=await fetch("/api/courses/"+course.id+"/publish",{method:"POST",headers});let published=await response.json();if(!response.ok)throw new Error(published.detail||"Kurs e’lon qilinmadi");
  $("#teacherPublishMessage").textContent="Kurs muvaffaqiyatli joylandi!";e.currentTarget.reset();$("#publishPriceWrap").classList.add("hidden");await loadCourses();setTimeout(closeTeacherPublish,900);
 }catch(err){$("#teacherPublishMessage").textContent=err.message}
 finally{button.disabled=false;button.textContent="Kursni joylash"}
});
loadCourses();