import { Modal } from 'antd'

interface PopupFormProps {
  modalVisible: boolean
  onCancel: () => void
  formTitle: string
  children: React.ReactNode
}

const PopupForm: React.FC<PopupFormProps> = ({
  modalVisible,
  onCancel,
  formTitle,
  children,
}) => {
  return (
    <Modal
      title={formTitle}
      open={modalVisible}
      onCancel={onCancel}
      footer={null}
      destroyOnClose
    >
      {children}
    </Modal>
  )
}

export default PopupForm
