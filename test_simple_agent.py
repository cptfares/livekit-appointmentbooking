from __future__ import annotations
import datetime
import logging
import os
import sys
from dataclasses import dataclass
from typing import Literal
from zoneinfo import ZoneInfo

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from calendar_api import AvailableSlot, FakeCalendar, SlotUnavailableError
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import openai, azure, elevenlabs, silero

load_dotenv()

@dataclass
class ClientData:
    cal: FakeCalendar
    full_name: str = ""
    phone_number: str = ""
    email: str = ""
    service_type: str = ""
    case_details: str = ""
    urgency: str = ""
    location: str = ""
    budget: str = ""
    preferred_contact: str = ""
    data_collected: bool = False

logger = logging.getLogger("shura-legal")

class SimpleShuraLegalAgent(Agent):
    def __init__(self, *, timezone: str) -> None:
        self.tz = ZoneInfo(timezone)
        today = datetime.datetime.now(self.tz).strftime("%A, %B %d, %Y")
        
        super().__init__(
            instructions=(
                f"أنت وكيل نصي تمثل منصة شورى للخدمات القانونية - منصة سعودية إلكترونية تقدم خدمات واستشارات قانونية. "
                f"اليوم هو {today}. "
                "أسلوبك: ودود، مطمئن، سهل الفهم باللهجة السعودية، مع صورة مهنية واضحة. "
                
                "ابدأ المحادثة بالتحية: "
                "'السلام عليكم! يعطيك العافية ومرحبا بك في شورى للخدمات القانونية. أنا مساعدك الذكي وموجود هنا عشان أساعدك.' "
                "ثم مباشرة: 'ممكن أعرف اسمك الكريم؟' "
                
                "خدمات شورى تشمل: استشارات قانونية، صياغة ومراجعة العقود، إعداد مذكرات قانونية، التمثيل القضائي، التوثيق القانوني، الترجمة القانونية، دراسة وتحليل القضايا. "
                
                "الأسعار: "
                "- الاستشارة الأساسية: مئة وتسعة وأربعين ريال (عشرين دقيقة مع محامي مرخص) "
                "- الاستشارة الذهبية: أربعمية وتسعة وتسعين ريال "
                "- الاستشارة البلاتينية: تسعمية وتسعة وتسعين ريال (خمسين دقيقة مع محامي بخبرة أكثر من عشر سنوات) "
                
                "جميع المحامين مرخصون من وزارة العدل وأعضاء في الهيئة السعودية للمحامين. "
                "طرق الدفع: مدى، أبل باي، فيزا، ماستر كارد، والتقسيط عبر تمارا. "
                
                "عند طلب موعد للاستشارة، استخدم وظائف جدولة المواعيد المتاحة. "
                
                "اختم دائماً: 'يعطيك العافية، خلال أربع وعشرين ساعة بنتواصل معك ونربطك بالمحامي المناسب.' "
            )
        )
        self._slots_map: dict[str, AvailableSlot] = {}

    def _required_fields(self) -> list[str]:
        return ["full_name", "phone_number", "email", "service_type"]

    def _missing_fields(self, ctx: RunContext["ClientData"]) -> list[str]:
        fields = self._required_fields()
        return [f for f in fields if not getattr(ctx.userdata, f, "").strip()]

    def _arabic_label(self, field: str) -> str:
        labels = {
            "full_name": "الاسم الثلاثي",
            "phone_number": "رقم الجوال",
            "email": "البريد الإلكتروني",
            "service_type": "نوع الخدمة المطلوبة",
        }
        return labels.get(field, field)

    @function_tool
    async def schedule_consultation(
        self,
        ctx: RunContext["ClientData"],
        slot_id: str,
        consultation_type: Literal["basic", "gold", "platinum"] = "basic"
    ) -> str | None:
        """
        Schedule a legal consultation appointment at the given slot.
        """
        slot = self._slots_map.get(slot_id)
        if not slot:
            return f"خطأ: رقم الموعد {slot_id} غير معروف. فضلاً اطلب عرض المواعيد المتاحة ثم اختر الرقم الظاهر بجانب الموعد."

        missing = self._missing_fields(ctx)
        if missing:
            missing_ar = "، ".join(self._arabic_label(f) for f in missing)
            return f"قبل الحجز نحتاج نكمل البيانات الأساسية: {missing_ar}. تقدر تزوّدني بها الآن؟"

        ctx.userdata.data_collected = True
        ctx.disallow_interruptions()

        try:
            await ctx.userdata.cal.schedule_appointment(
                start_time=slot.start_time,
                attendee_email=ctx.userdata.email,
                attendee_name=ctx.userdata.full_name,
            )
        except SlotUnavailableError:
            return "عذراً، هذا الموعد لم يعد متاحاً. هل تود أستعرض لك مواعيد أخرى قريبة؟"

        local = slot.start_time.astimezone(self.tz)
        price_map = {
            "basic": "مئة وتسعة وأربعين ريال",
            "gold": "أربعمية وتسعة وتسعين ريال",
            "platinum": "تسعمية وتسعة وتسعين ريال",
        }

        return (
            f"تم حجز موعد الاستشارة بنجاح يوم {local.strftime('%A')} "
            f"تاريخ {local.strftime('%d %B %Y')} الساعة {local.strftime('%H:%M')}. "
            f"نوع الاستشارة: {consultation_type} بقيمة {price_map[consultation_type]}. "
            f"بإذن الله راح نتواصل معك خلال أربع وعشرين ساعة."
        )

    @function_tool
    async def list_available_slots(
        self, 
        ctx: RunContext[ClientData], 
        range: Literal["+2week", "+1month", "+3month", "default"] = "default"
    ) -> str:
        """
        Return available consultation slots in Arabic.
        """
        now = datetime.datetime.now(self.tz)
        lines: list[str] = []
        
        if range == "+2week" or range == "default":
            range_days = 14
        elif range == "+1month":
            range_days = 30
        elif range == "+3month":
            range_days = 90

        for slot in await ctx.userdata.cal.list_available_slots(
            start_time=now, 
            end_time=now + datetime.timedelta(days=range_days)
        ):
            local = slot.start_time.astimezone(self.tz)
            delta = local - now
            days = delta.days
            
            if local.date() == now.date():
                rel = "اليوم"
            elif local.date() == (now.date() + datetime.timedelta(days=1)):
                rel = "بكرة"
            elif days < 7:
                rel = f"خلال {days} أيام"
            elif days < 14:
                rel = "خلال أسبوع"
            else:
                rel = f"خلال {days // 7} أسابيع"

            day_names = {
                'Monday': 'الاثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء',
                'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'
            }
            
            arabic_day = day_names.get(local.strftime('%A'), local.strftime('%A'))
            
            lines.append(
                f"{slot.unique_hash} – {arabic_day} "
                f"{local.strftime('%d/%m/%Y')} الساعة {local.strftime('%H:%M')} ({rel})"
            )
            self._slots_map[slot.unique_hash] = slot

        return "\n".join(lines) or "لا توجد مواعيد متاحة في الوقت الحالي."

    @function_tool
    async def collect_client_data(
        self,
        ctx: RunContext["ClientData"],
        full_name: str = "",
        phone_number: str = "",
        email: str = "",
        service_type: str = "",
        case_details: str = "",
        urgency: str = "",
        location: str = "",
        budget: str = "",
        preferred_contact: str = ""
    ) -> str:
        if full_name:
            ctx.userdata.full_name = full_name.strip()
        if phone_number:
            ctx.userdata.phone_number = phone_number.strip()
        if email:
            ctx.userdata.email = email.strip()
        if service_type:
            ctx.userdata.service_type = service_type.strip()
        if case_details:
            ctx.userdata.case_details = case_details.strip()
        if urgency:
            ctx.userdata.urgency = urgency.strip()
        if location:
            ctx.userdata.location = location.strip()
        if budget:
            ctx.userdata.budget = budget.strip()
        if preferred_contact:
            ctx.userdata.preferred_contact = preferred_contact.strip()

        missing = self._missing_fields(ctx)
        ctx.userdata.data_collected = len(missing) == 0

        if ctx.userdata.data_collected:
            return "تم حفظ بياناتك الأساسية بالكامل. نقدر الآن نكمل حجز موعد الاستشارة. هل تفضل أستعرض لك المواعيد المتاحة؟"

        missing_ar = "، ".join(self._arabic_label(f) for f in missing)
        return f"تم حفظ البيانات المتاحة. المتبقي: {missing_ar}. تفضل عطنا المعلومات الناقصة عشان نكمل الحجز."


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    timezone = "Asia/Riyadh"
    
    # Use FakeCalendar for testing
    cal = FakeCalendar(timezone=timezone)
    await cal.initialize()

    session = AgentSession[ClientData](
        userdata=ClientData(cal=cal),
        stt=azure.STT(
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION"),
            language=["ar-SA"]  # Arabic (Saudi Arabia)
        ),
        llm=openai.LLM(model="gpt-4o", parallel_tool_calls=False, temperature=0.45),
        tts=elevenlabs.TTS(voice_id="3nav5pHC1EYvWOd5LmnA", model="eleven_multilingual_v2"),
        vad=silero.VAD.load(),
        max_tool_steps=1,
    )

    await session.start(agent=SimpleShuraLegalAgent(timezone=timezone), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
