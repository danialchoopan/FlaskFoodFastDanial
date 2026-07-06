class OrderStatus:
    WAITING_CONFIRMATION = "در انتظار تایید رستوران"
    CONFIRMED = "تایید رستوران"
    PREPARING = "در حال آماده‌سازی"
    COMPLETED = "سفارش شما تکمیل شد"
    CANCELLED_BY_SELLER = "لغو رستوران"
    CANCELLED_BY_USER = "لغو کاربر"

    @classmethod
    def all(cls):
        return [
            cls.WAITING_CONFIRMATION, cls.CONFIRMED, cls.PREPARING,
            cls.COMPLETED, cls.CANCELLED_BY_SELLER, cls.CANCELLED_BY_USER,
        ]

    @classmethod
    def active_statuses(cls):
        return [cls.WAITING_CONFIRMATION, cls.CONFIRMED, cls.PREPARING]

    @classmethod
    def is_terminal(cls, status):
        return status in [cls.COMPLETED, cls.CANCELLED_BY_SELLER, cls.CANCELLED_BY_USER]

    @classmethod
    def css_class(cls, status):
        if status == cls.COMPLETED:
            return "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
        elif status in (cls.CANCELLED_BY_SELLER, cls.CANCELLED_BY_USER):
            return "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
        elif status == cls.PREPARING:
            return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
        elif status == cls.CONFIRMED:
            return "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"
        else:
            return "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
