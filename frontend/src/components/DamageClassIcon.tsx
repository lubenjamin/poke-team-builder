const ICON_BY_DAMAGE_CLASS: Record<string, string> = {
  physical: "/damage-icons/physical.webp",
  special: "/damage-icons/special.webp",
  status: "/damage-icons/status.webp",
};

interface DamageClassIconProps {
  damageClass: string;
  size?: number;
}

export function DamageClassIcon({ damageClass, size = 18 }: DamageClassIconProps) {
  const src = ICON_BY_DAMAGE_CLASS[damageClass];
  if (!src) return null;

  return (
    <img
      src={src}
      alt={damageClass}
      title={damageClass}
      width={size}
      height={size}
      style={{ display: "inline-block", verticalAlign: "middle" }}
    />
  );
}
