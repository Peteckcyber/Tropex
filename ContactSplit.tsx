import React from 'react';
import { Mail, MapPin, Phone, Printer } from 'lucide-react';

type ContactSplitProps = {
  title?: string;
  phone?: string;
  fax?: string;
  email?: string;
  imageSrc?: string;
  imageAlt?: string;
};

const contactRows = ({
  phone,
  fax,
  email,
}: Required<Pick<ContactSplitProps, 'phone' | 'fax' | 'email'>>) => [
  {
    key: 'phone',
    label: 'Tel:',
    icon: Phone,
    value: (
      <a href={`tel:${phone.replace(/\s+/g, '')}`}>
        {phone}
      </a>
    ),
  },
  {
    key: 'fax',
    label: 'Fax:',
    icon: Printer,
    value: <span>{fax}</span>,
  },
  {
    key: 'email',
    label: 'E-mail:',
    icon: Mail,
    value: <a href={`mailto:${email}`}>{email}</a>,
  },
  {
    key: 'address',
    label: 'Address:',
    icon: MapPin,
    value: (
      <>
        <div className="block">No. 1168, Huanghe 40 Road,</div>
        <div className="block">Bincheng District,</div>
        <div className="block">Binzhou City</div>
      </>
    ),
  },
];

export default function ContactSplit({
  title = 'Tropex Metal Products Co., Ltd. Headquarter',
  phone = '+852 5686 4074',
  fax = '+852 5686 4074',
  email = 'info@tropexltdchina.com',
  imageSrc = '/assets/images/contact/contact-office.png',
  imageAlt = 'Tropex Metal Products Co., Ltd. office interior',
}: ContactSplitProps) {
  const rows = contactRows({ phone, fax, email });

  return (
    <section className="w-full">
      <div className="w-full flex flex-col md:flex-row items-stretch">
        <div className="w-full md:w-1/2 bg-[#1b4f86] p-6 text-white sm:p-10 md:p-16">
          <h2 className="m-0 text-[1.55rem] font-extrabold leading-[1.25] tracking-[0.02em] text-[#c13333]">
            {title}
          </h2>

          <hr className="mt-4 w-full border-t border-white/20" />

          <div className="mt-8 space-y-6">
            {rows.map(({ key, label, icon: Icon, value }) => (
              <div key={key} className="flex items-start gap-4">
                <span className="flex h-12 w-12 items-center justify-center border border-white/40 rounded-full p-2 flex-shrink-0 text-white">
                  <Icon className="h-5 w-5" strokeWidth={1.8} />
                </span>

                <div className="flex items-start flex-1 text-sm md:text-base leading-relaxed text-white">
                  <span className="w-20 font-bold whitespace-nowrap flex-shrink-0">
                    {label}
                  </span>
                  <div className="flex-1 font-medium text-white/90">
                    {value}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="w-full md:w-1/2 relative min-h-[350px] md:min-h-full">
          <img
            src={imageSrc}
            alt={imageAlt}
            className="absolute inset-0 w-full h-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-black/5 mix-blend-multiply" aria-hidden="true" />
        </div>
      </div>
    </section>
  );
}
